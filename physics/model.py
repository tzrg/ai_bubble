"""Flash evaporation droplet model with ODE system.

This model implements TRUE flash boiling physics:
- Surface evaporation via Hertz-Knudsen equation
- Internal nucleate boiling when superheated
- Droplet fragmentation/explosion at high superheat
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from scipy.integrate import solve_ivp

from .properties import WaterProperties


@dataclass
class SimulationParameters:
    """Parameters for flash evaporation simulation."""
    
    # Initial conditions
    R0: float = 1.0e-3  # Initial radius [m] (1 mm)
    T0: float = 373.0  # Initial temperature [K] - default to boiling point
    
    # Ambient conditions
    p_ambient: float = 1000.0  # Ambient pressure [Pa] (very low = strong flash)
    T_ambient: float = 300.0  # Ambient temperature [K] (for convection)
    
    # Model parameters
    alpha: float = 0.5  # Evaporation coefficient [-] (0.01 to 1.0) - higher for flash
    include_convection: bool = False  # Include convective heat transfer
    h_conv: float = 10.0  # Convective heat transfer coefficient [W/(m²·K)]
    
    # Flash boiling parameters
    enable_nucleate_boiling: bool = True  # Enable internal boiling
    superheat_threshold: float = 5.0  # Superheat [K] to trigger nucleate boiling
    nucleation_factor: float = 10.0  # Multiplier for nucleate boiling rate
    fragmentation_superheat: float = 30.0  # Superheat [K] for explosive fragmentation
    
    # Simulation settings
    t_max: float = 1.0  # Maximum simulation time [s] - flash is fast!
    n_points: int = 1000  # Number of output points
    
    def validate(self) -> None:
        """Validate parameter ranges."""
        assert self.R0 > 0, "Initial radius must be positive"
        assert self.T0 > WaterProperties.T_FREEZE, "Initial temperature must be above freezing"
        assert self.T0 < WaterProperties.T_CRITICAL, "Initial temperature must be below critical"
        assert self.p_ambient >= 0, "Ambient pressure must be non-negative"
        assert 0 < self.alpha <= 1.0, "Evaporation coefficient must be in (0, 1]"


@dataclass
class SimulationResult:
    """Results from flash evaporation simulation."""
    
    t: np.ndarray  # Time array [s]
    R: np.ndarray  # Radius array [m]
    T: np.ndarray  # Temperature array [K]
    m_dot: np.ndarray  # Evaporation rate array [kg/s]
    p_sat: np.ndarray  # Saturation pressure array [Pa]
    superheat: np.ndarray  # Superheat degree array [K]
    fragmented: bool = False  # Whether droplet fragmented
    fragmentation_time: float = None  # Time of fragmentation [s]
    
    @property
    def mass(self) -> np.ndarray:
        """Droplet mass [kg]."""
        rho = WaterProperties.liquid_density(self.T[0])
        return (4.0/3.0) * np.pi * self.R**3 * rho
    
    @property
    def R_mm(self) -> np.ndarray:
        """Radius in millimeters."""
        return self.R * 1000.0
    
    @property
    def T_celsius(self) -> np.ndarray:
        """Temperature in Celsius."""
        return self.T - 273.15
    
    @property
    def evaporation_complete(self) -> bool:
        """Check if droplet fully evaporated."""
        return self.R[-1] < 1e-9 or self.fragmented


class FlashEvaporationModel:
    """
    Physical model for flash boiling of a liquid droplet.
    
    Implements true flash evaporation physics:
    - Surface evaporation via Hertz-Knudsen equation
    - Internal nucleate boiling when droplet is superheated
    - Explosive fragmentation at high superheat degrees
    
    Solves coupled ODEs for droplet radius and temperature:
    - dR/dt: Mass balance with combined evaporation mechanisms
    - dT/dt: Energy balance with latent heat removal
    """
    
    def __init__(self, params: Optional[SimulationParameters] = None):
        """
        Initialize the model.
        
        Parameters
        ----------
        params : SimulationParameters, optional
            Simulation parameters. Uses defaults if not provided.
        """
        self.params = params or SimulationParameters()
        self.props = WaterProperties
        self._fragmented = False
        self._fragmentation_time = None
    
    def saturation_temperature(self, p: float) -> float:
        """
        Calculate saturation temperature at given pressure.
        
        Inverse of Antoine equation.
        
        Parameters
        ----------
        p : float
            Pressure [Pa]
            
        Returns
        -------
        float
            Saturation temperature [K]
        """
        # Convert Pa to mmHg
        p_mmhg = p / 133.322
        if p_mmhg <= 0:
            return 273.15  # Return freezing point for zero/negative pressure
        
        # Inverse Antoine: T = B / (A - log10(p)) - C
        A, B, C = self.props.ANTOINE_A, self.props.ANTOINE_B, self.props.ANTOINE_C
        log_p = np.log10(p_mmhg)
        T_celsius = B / (A - log_p) - C
        return T_celsius + 273.15
    
    def superheat_degree(self, T: float) -> float:
        """
        Calculate superheat degree.
        
        Superheat = T_droplet - T_sat(p_ambient)
        
        Parameters
        ----------
        T : float
            Droplet temperature [K]
            
        Returns
        -------
        float
            Superheat degree [K] (positive = superheated)
        """
        T_sat = self.saturation_temperature(self.params.p_ambient)
        return T - T_sat
    
    def surface_evaporation_rate(self, R: float, T: float) -> float:
        """
        Calculate surface evaporation rate using Hertz-Knudsen equation.
        
        ṁ_surface = 4πR² · α · (p_sat - p_∞) / √(2π·R_s·T)
        
        Parameters
        ----------
        R : float
            Droplet radius [m]
        T : float
            Droplet temperature [K]
            
        Returns
        -------
        float
            Mass evaporation rate [kg/s]
        """
        if R <= 0 or T <= 0:
            return 0.0
            
        p_sat = self.props.saturation_pressure(T)
        p_diff = p_sat - self.params.p_ambient
        
        # No evaporation if ambient pressure exceeds saturation
        if p_diff <= 0:
            return 0.0
        
        # Hertz-Knudsen equation
        A = 4.0 * np.pi * R**2  # Surface area
        denom = np.sqrt(2.0 * np.pi * self.props.R_SPECIFIC * T)
        m_dot = A * self.params.alpha * p_diff / denom
        
        return m_dot
    
    def nucleate_boiling_rate(self, R: float, T: float) -> float:
        """
        Calculate internal nucleate boiling rate.
        
        When the droplet is superheated, bubbles nucleate inside and
        cause rapid volumetric evaporation, not just surface evaporation.
        
        Rate scales with superheat degree squared (empirical correlation).
        
        Parameters
        ----------
        R : float
            Droplet radius [m]
        T : float
            Droplet temperature [K]
            
        Returns
        -------
        float
            Additional mass evaporation rate from nucleate boiling [kg/s]
        """
        if not self.params.enable_nucleate_boiling:
            return 0.0
        
        superheat = self.superheat_degree(T)
        
        if superheat <= self.params.superheat_threshold:
            return 0.0
        
        # Nucleate boiling rate scales with superheat^2 and volume
        # This is based on pool boiling correlations adapted for droplets
        effective_superheat = superheat - self.params.superheat_threshold
        
        # Volume-based evaporation (internal boiling)
        rho = self.props.liquid_density(T)
        volume = (4.0/3.0) * np.pi * R**3
        mass = volume * rho
        
        # Characteristic time for nucleate boiling (empirical)
        # Higher superheat = faster boiling
        # tau ~ 1 / (superheat^2) for violent boiling
        tau = 0.01 / (1.0 + (effective_superheat / 10.0)**2)
        
        m_dot_nucleate = self.params.nucleation_factor * mass / tau * (effective_superheat / 100.0)
        
        return m_dot_nucleate
    
    def evaporation_rate(self, R: float, T: float) -> float:
        """
        Calculate total mass evaporation rate.
        
        Combines surface evaporation and nucleate boiling.
        
        Parameters
        ----------
        R : float
            Droplet radius [m]
        T : float
            Droplet temperature [K]
            
        Returns
        -------
        float
            Total mass evaporation rate [kg/s]
        """
        m_dot_surface = self.surface_evaporation_rate(R, T)
        m_dot_nucleate = self.nucleate_boiling_rate(R, T)
        
        return m_dot_surface + m_dot_nucleate
    
    def convective_heat(self, R: float, T: float) -> float:
        """
        Calculate convective heat transfer rate.
        
        Q̇ = h·A·(T_∞ - T)
        
        Parameters
        ----------
        R : float
            Droplet radius [m]
        T : float
            Droplet temperature [K]
            
        Returns
        -------
        float
            Heat transfer rate [W] (positive = heating)
        """
        if not self.params.include_convection or R <= 0:
            return 0.0
            
        A = 4.0 * np.pi * R**2
        return self.params.h_conv * A * (self.params.T_ambient - T)
    
    def check_fragmentation(self, T: float, t: float) -> bool:
        """
        Check if droplet should fragment due to explosive boiling.
        
        At very high superheat, bubble growth is so rapid that the
        droplet shatters into many smaller droplets.
        
        Parameters
        ----------
        T : float
            Droplet temperature [K]
        t : float
            Current time [s]
            
        Returns
        -------
        bool
            True if fragmentation occurs
        """
        if self._fragmented:
            return True
            
        superheat = self.superheat_degree(T)
        
        if superheat >= self.params.fragmentation_superheat:
            self._fragmented = True
            self._fragmentation_time = t
            return True
        
        return False
    
    def ode_system(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        ODE system for flash evaporation.
        
        State vector y = [R, T]
        
        Parameters
        ----------
        t : float
            Time [s]
        y : np.ndarray
            State vector [R, T]
            
        Returns
        -------
        np.ndarray
            Derivatives [dR/dt, dT/dt]
        """
        R, T = y
        
        # Clamp to physical bounds
        if R <= 1e-12:
            return np.array([0.0, 0.0])
        
        # Check for fragmentation
        if self.check_fragmentation(T, t):
            # Rapid disintegration after fragmentation
            rho = self.props.liquid_density(T)
            # Assume fragments evaporate ~100x faster due to increased surface area
            return np.array([-R * 100.0, -50.0])  # Very fast radius decrease
        
        T = np.clip(T, self.props.T_FREEZE + 1.0, self.props.T_CRITICAL - 1.0)
        
        # Get properties
        rho = self.props.liquid_density(T)
        cp = self.props.specific_heat(T)
        h_fg = self.props.latent_heat(T)
        
        # Evaporation rate (surface + nucleate boiling)
        m_dot = self.evaporation_rate(R, T)
        
        # Mass balance: dR/dt = -ṁ / (4πR²ρ)
        dR_dt = -m_dot / (4.0 * np.pi * R**2 * rho)
        
        # Energy balance: m·cp·dT/dt = -ṁ·h_fg + Q̇_conv
        mass = (4.0/3.0) * np.pi * R**3 * rho
        Q_conv = self.convective_heat(R, T)
        
        if mass > 1e-15:
            dT_dt = (-m_dot * h_fg + Q_conv) / (mass * cp)
        else:
            dT_dt = 0.0
        
        return np.array([dR_dt, dT_dt])
    
    def termination_event(self, t: float, y: np.ndarray) -> float:
        """Event function for terminating integration when droplet vanishes."""
        R = y[0]
        return R - 1e-9  # Terminate when R approaches zero
    
    termination_event.terminal = True
    termination_event.direction = -1
    
    def freezing_event(self, t: float, y: np.ndarray) -> float:
        """Event function for detecting freezing."""
        T = y[1]
        return T - self.props.T_FREEZE
    
    freezing_event.terminal = True
    freezing_event.direction = -1
    
    def solve(self) -> SimulationResult:
        """
        Solve the flash evaporation problem.
        
        Returns
        -------
        SimulationResult
            Simulation results including time histories
        """
        self.params.validate()
        
        # Reset fragmentation state
        self._fragmented = False
        self._fragmentation_time = None
        
        # Initial state
        y0 = np.array([self.params.R0, self.params.T0])
        t_span = (0.0, self.params.t_max)
        t_eval = np.linspace(0.0, self.params.t_max, self.params.n_points)
        
        # Solve ODE system with tighter tolerances for fast dynamics
        sol = solve_ivp(
            self.ode_system,
            t_span,
            y0,
            method='RK45',
            t_eval=t_eval,
            events=[self.termination_event, self.freezing_event],
            dense_output=True,
            rtol=1e-10,
            atol=1e-12,
            max_step=self.params.t_max / 1000  # Ensure fine time resolution
        )
        
        # Extract results
        t = sol.t
        R = sol.y[0]
        T = sol.y[1]
        
        # Clamp negative values
        R = np.maximum(R, 0.0)
        T = np.maximum(T, self.props.T_FREEZE)
        
        # Calculate derived quantities
        m_dot = np.array([self.evaporation_rate(r, temp) for r, temp in zip(R, T)])
        p_sat = np.array([self.props.saturation_pressure(temp) for temp in T])
        superheat = np.array([self.superheat_degree(temp) for temp in T])
        
        return SimulationResult(
            t=t,
            R=R,
            T=T,
            m_dot=m_dot,
            p_sat=p_sat,
            superheat=superheat,
            fragmented=self._fragmented,
            fragmentation_time=self._fragmentation_time
        )


def run_example():
    """Run an example simulation demonstrating flash boiling."""
    # True flash boiling scenario:
    # Hot water (80°C) suddenly exposed to very low pressure (1 kPa)
    # This creates ~40K superheat -> explosive evaporation
    params = SimulationParameters(
        R0=1.0e-3,  # 1 mm droplet
        T0=373.0,  # 100°C (boiling at 1 atm)
        p_ambient=1000.0,  # 1 kPa (very low pressure)
        alpha=0.5,  # Higher evaporation coefficient
        enable_nucleate_boiling=True,
        superheat_threshold=5.0,
        fragmentation_superheat=30.0,
        t_max=0.1  # 100 ms - flash is fast!
    )
    
    model = FlashEvaporationModel(params)
    
    # Calculate initial superheat
    T_sat = model.saturation_temperature(params.p_ambient)
    superheat = params.T0 - T_sat
    print(f"Initial conditions:")
    print(f"  T_droplet = {params.T0:.1f} K ({params.T0-273.15:.1f} °C)")
    print(f"  T_sat at {params.p_ambient} Pa = {T_sat:.1f} K ({T_sat-273.15:.1f} °C)")
    print(f"  Superheat = {superheat:.1f} K")
    print()
    
    result = model.solve()
    
    print(f"Simulation completed:")
    print(f"  Final time: {result.t[-1]*1000:.2f} ms")
    print(f"  Final radius: {result.R_mm[-1]:.4f} mm")
    print(f"  Final temperature: {result.T_celsius[-1]:.2f} °C")
    print(f"  Fragmented: {result.fragmented}")
    if result.fragmented:
        print(f"  Fragmentation time: {result.fragmentation_time*1000:.2f} ms")
    print(f"  Evaporation complete: {result.evaporation_complete}")
    
    return result


if __name__ == "__main__":
    run_example()
