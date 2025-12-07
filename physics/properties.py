"""Thermodynamic properties for water/steam."""

import numpy as np


class WaterProperties:
    """
    Thermodynamic properties of water for flash evaporation calculations.
    
    Uses Antoine equation for saturation pressure and temperature-dependent
    correlations for other properties.
    """
    
    # Physical constants
    R_GAS = 8.314462  # Universal gas constant [J/(mol·K)]
    M_WATER = 18.015e-3  # Molar mass of water [kg/mol]
    R_SPECIFIC = R_GAS / M_WATER  # Specific gas constant [J/(kg·K)]
    
    # Antoine equation coefficients for water (valid ~273-473 K)
    # log10(p_sat [mmHg]) = A - B / (C + T [°C])
    ANTOINE_A = 8.07131
    ANTOINE_B = 1730.63
    ANTOINE_C = 233.426
    
    # Reference values for Clausius-Clapeyron
    T_REF = 373.15  # Reference temperature [K] (boiling at 1 atm)
    P_REF = 101325.0  # Reference pressure [Pa]
    H_FG_REF = 2257e3  # Latent heat at T_REF [J/kg]
    
    # Liquid water properties (approximate, weakly T-dependent)
    RHO_LIQUID = 1000.0  # Density [kg/m³]
    CP_LIQUID = 4186.0  # Specific heat capacity [J/(kg·K)]
    
    # Temperature limits
    T_FREEZE = 273.15  # Freezing point [K]
    T_CRITICAL = 647.1  # Critical temperature [K]
    
    @classmethod
    def saturation_pressure_antoine(cls, T: float) -> float:
        """
        Calculate saturation pressure using Antoine equation.
        
        Parameters
        ----------
        T : float
            Temperature [K]
            
        Returns
        -------
        float
            Saturation pressure [Pa]
        """
        T_celsius = T - 273.15
        # Antoine gives pressure in mmHg
        log_p_mmhg = cls.ANTOINE_A - cls.ANTOINE_B / (cls.ANTOINE_C + T_celsius)
        p_mmhg = 10.0 ** log_p_mmhg
        # Convert mmHg to Pa (1 mmHg = 133.322 Pa)
        return p_mmhg * 133.322
    
    @classmethod
    def saturation_pressure_clausius(cls, T: float) -> float:
        """
        Calculate saturation pressure using Clausius-Clapeyron equation.
        
        Parameters
        ----------
        T : float
            Temperature [K]
            
        Returns
        -------
        float
            Saturation pressure [Pa]
        """
        exponent = (cls.H_FG_REF * cls.M_WATER / cls.R_GAS) * (1.0/cls.T_REF - 1.0/T)
        return cls.P_REF * np.exp(exponent)
    
    @classmethod
    def saturation_pressure(cls, T: float) -> float:
        """
        Calculate saturation pressure (uses Antoine equation).
        
        Parameters
        ----------
        T : float
            Temperature [K]
            
        Returns
        -------
        float
            Saturation pressure [Pa]
        """
        return cls.saturation_pressure_antoine(T)
    
    @classmethod
    def latent_heat(cls, T: float) -> float:
        """
        Calculate latent heat of vaporization with temperature correction.
        
        Uses Watson correlation for temperature dependence.
        
        Parameters
        ----------
        T : float
            Temperature [K]
            
        Returns
        -------
        float
            Latent heat of vaporization [J/kg]
        """
        # Watson correlation exponent
        n = 0.38
        T_r = T / cls.T_CRITICAL
        T_r_ref = cls.T_REF / cls.T_CRITICAL
        
        if T >= cls.T_CRITICAL:
            return 0.0
        
        h_fg = cls.H_FG_REF * ((1.0 - T_r) / (1.0 - T_r_ref)) ** n
        return max(h_fg, 0.0)
    
    @classmethod
    def liquid_density(cls, T: float) -> float:
        """
        Calculate liquid water density.
        
        Uses simplified correlation valid for 273-373 K.
        
        Parameters
        ----------
        T : float
            Temperature [K]
            
        Returns
        -------
        float
            Liquid density [kg/m³]
        """
        # Simplified quadratic fit
        T_c = T - 273.15
        rho = 1000.0 - 0.0178 * abs(T_c - 4.0) ** 1.7
        return max(rho, 500.0)  # Lower bound for safety
    
    @classmethod
    def specific_heat(cls, T: float) -> float:
        """
        Calculate liquid specific heat capacity.
        
        Parameters
        ----------
        T : float
            Temperature [K]
            
        Returns
        -------
        float
            Specific heat capacity [J/(kg·K)]
        """
        # Weakly temperature dependent, use constant for simplicity
        return cls.CP_LIQUID
