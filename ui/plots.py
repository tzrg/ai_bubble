"""PyQtGraph-based plotting widgets for simulation results."""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from physics.model import SimulationResult


# Configure pyqtgraph
pg.setConfigOptions(antialias=True, background='w', foreground='k')


class SimulationPlots(QWidget):
    """Widget containing all simulation result plots."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the plotting UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Create plot widgets
        self.radius_plot = pg.PlotWidget(title="Droplet Radius vs Time")
        self.temp_plot = pg.PlotWidget(title="Droplet Temperature vs Time")
        self.evap_plot = pg.PlotWidget(title="Evaporation Rate vs Time")
        self.pressure_plot = pg.PlotWidget(title="Saturation Pressure vs Time")
        
        # Configure plots
        self._configure_plot(self.radius_plot, "Time [s]", "Radius [mm]")
        self._configure_plot(self.temp_plot, "Time [s]", "Temperature [K]")
        self._configure_plot(self.evap_plot, "Time [s]", "ṁ [kg/s]")
        self._configure_plot(self.pressure_plot, "Time [s]", "p_sat [Pa]")
        
        # Create plot curves
        pen_radius = pg.mkPen(color='#2196F3', width=2)
        pen_temp = pg.mkPen(color='#F44336', width=2)
        pen_evap = pg.mkPen(color='#4CAF50', width=2)
        pen_psat = pg.mkPen(color='#9C27B0', width=2)
        pen_pamb = pg.mkPen(color='#FF9800', width=2, style=Qt.PenStyle.DashLine)
        
        self.radius_curve = self.radius_plot.plot([], [], pen=pen_radius)
        self.temp_curve = self.temp_plot.plot([], [], pen=pen_temp)
        self.evap_curve = self.evap_plot.plot([], [], pen=pen_evap)
        self.psat_curve = self.pressure_plot.plot([], [], pen=pen_psat, name="p_sat")
        self.pamb_line = None  # Will be added as infinite line
        
        # Arrange in 2x2 grid
        top_row = QHBoxLayout()
        top_row.addWidget(self.radius_plot)
        top_row.addWidget(self.temp_plot)
        
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.evap_plot)
        bottom_row.addWidget(self.pressure_plot)
        
        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        
        # Status label
        self.status_label = QLabel("Ready - adjust parameters and run simulation")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)
    
    def _configure_plot(self, plot: pg.PlotWidget, x_label: str, y_label: str):
        """Configure a plot widget with labels and styling."""
        plot.setLabel('bottom', x_label)
        plot.setLabel('left', y_label)
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setMinimumHeight(200)
        
        # Style the plot
        plot.getAxis('bottom').setStyle(tickFont=QFont("Arial", 9))
        plot.getAxis('left').setStyle(tickFont=QFont("Arial", 9))
    
    def update_plots(self, result: SimulationResult, p_ambient: float):
        """
        Update all plots with simulation results.
        
        Parameters
        ----------
        result : SimulationResult
            Simulation results to plot
        p_ambient : float
            Ambient pressure for reference line
        """
        # Update curves
        self.radius_curve.setData(result.t, result.R_mm)
        self.temp_curve.setData(result.t, result.T)
        self.evap_curve.setData(result.t, result.m_dot)
        self.psat_curve.setData(result.t, result.p_sat)
        
        # Add/update ambient pressure reference line
        if self.pamb_line is not None:
            self.pressure_plot.removeItem(self.pamb_line)
        self.pamb_line = pg.InfiniteLine(
            pos=p_ambient,
            angle=0,
            pen=pg.mkPen(color='#FF9800', width=2, style=Qt.PenStyle.DashLine),
            label=f'p_ambient = {p_ambient:.0f} Pa',
            labelOpts={'position': 0.1, 'color': '#FF9800'}
        )
        self.pressure_plot.addItem(self.pamb_line)
        
        # Auto-range plots
        self.radius_plot.autoRange()
        self.temp_plot.autoRange()
        self.evap_plot.autoRange()
        self.pressure_plot.autoRange()
        
        # Update status
        if result.evaporation_complete:
            status = f"✓ Evaporation complete at t = {result.t[-1]:.3f} s"
        elif result.T[-1] <= 273.15:
            status = f"❄ Freezing reached at t = {result.t[-1]:.3f} s, T = {result.T[-1]:.1f} K"
        else:
            status = f"Simulation ended at t = {result.t[-1]:.3f} s (R = {result.R_mm[-1]:.4f} mm, T = {result.T[-1]:.1f} K)"
        
        self.status_label.setText(status)
    
    def clear_plots(self):
        """Clear all plot data."""
        self.radius_curve.setData([], [])
        self.temp_curve.setData([], [])
        self.evap_curve.setData([], [])
        self.psat_curve.setData([], [])
        if self.pamb_line is not None:
            self.pressure_plot.removeItem(self.pamb_line)
            self.pamb_line = None
        self.status_label.setText("Ready - adjust parameters and run simulation")
