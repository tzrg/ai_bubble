"""Flash evaporation droplet model with ODE system."""

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
    T0: float = 300.0  # Initial temperature [K]
    
    # Ambient conditions
    p_ambient: float = 1000.0  # Ambient pressure [Pa]
    T_ambient: float = 300.0  # Ambient temperature [K] (for convection)
    
    # Model parameters
    alpha: float = 0.1  # Evaporation coefficient [-] (0.01 to 1.0)
    include_convection: bool = False  # Include convective heat transfer
    h_conv: float = 10.0  # Convective heat transfer coefficient [W/(m²·K)]
    
    # Simulation settings
    t_max: float = 10.0  # Maximum simulation time [s]
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
        return self.R[-1] < 1e-9


class FlashEvaporationModel:
    """
    Physical model for flash evaporation of a liquid droplet.
    
    Solves coupled ODEs for droplet radius and temperature:
    - dR/dt: Mass balance with Hertz-Knudsen evaporation
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
        
    def evaporation_rate(self, R: float, T: float) -> float:
        """
        Calculate mass evaporation rate using Hertz-Knudsen equation.
        
        ṁ = 4πR² · α · (p_sat - p_∞) / √(2π·R_s·T)
        
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
        
        T = np.clip(T, self.props.T_FREEZE + 1.0, self.props.T_CRITICAL - 1.0)
        
        # Get properties
        rho = self.props.liquid_density(T)
        cp = self.props.specific_heat(T)
        h_fg = self.props.latent_heat(T)
        
        # Evaporation rate
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
        
        # Initial state
        y0 = np.array([self.params.R0, self.params.T0])
        t_span = (0.0, self.params.t_max)
        t_eval = np.linspace(0.0, self.params.t_max, self.params.n_points)
        
        # Solve ODE system
        sol = solve_ivp(
            self.ode_system,
            t_span,
            y0,
            method='RK45',
            t_eval=t_eval,
            events=[self.termination_event, self.freezing_event],
            dense_output=True,
            rtol=1e-8,
            atol=1e-10
        )
        
        # Extract results
        t = sol.t
        R = sol.y[0]
        T = sol.y[1]
        
        # Calculate derived quantities
        m_dot = np.array([self.evaporation_rate(r, temp) for r, temp in zip(R, T)])
        p_sat = np.array([self.props.saturation_pressure(temp) for temp in T])
        
        return SimulationResult(
            t=t,
            R=R,
            T=T,
            m_dot=m_dot,
            p_sat=p_sat
        )


def run_example():
    """Run an example simulation."""
    params = SimulationParameters(
        R0=1.0e-3,  # 1 mm
        T0=350.0,  # 77°C
        p_ambient=2000.0,  # 2 kPa (low vacuum)
        alpha=0.1
    )
    
    model = FlashEvaporationModel(params)
    result = model.solve()
    
    print(f"Simulation completed:")
    print(f"  Final time: {result.t[-1]:.4f} s")
    print(f"  Final radius: {result.R_mm[-1]:.4f} mm")
    print(f"  Final temperature: {result.T_celsius[-1]:.2f} °C")
    print(f"  Evaporation complete: {result.evaporation_complete}")
    
    return result


if __name__ == "__main__":
    run_example()
