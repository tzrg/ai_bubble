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
        self._result = None
        self._time_markers = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the plotting UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Create plot widgets
        self.radius_plot = pg.PlotWidget(title="Droplet Radius vs Time")
        self.temp_plot = pg.PlotWidget(title="Temperature & Superheat vs Time")
        self.evap_plot = pg.PlotWidget(title="Evaporation Rate vs Time")
        self.pressure_plot = pg.PlotWidget(title="Pressure vs Time")
        
        # Configure plots
        self._configure_plot(self.radius_plot, "Time [s]", "Radius [mm]")
        self._configure_plot(self.temp_plot, "Time [s]", "Temperature [K]")
        self._configure_plot(self.evap_plot, "Time [s]", "ṁ [kg/s]")
        self._configure_plot(self.pressure_plot, "Time [s]", "Pressure [Pa]")
        
        # Create plot curves
        pen_radius = pg.mkPen(color='#2196F3', width=2)
        pen_temp = pg.mkPen(color='#F44336', width=2)
        pen_superheat = pg.mkPen(color='#FF9800', width=2, style=Qt.PenStyle.DashLine)
        pen_evap = pg.mkPen(color='#4CAF50', width=2)
        pen_psat = pg.mkPen(color='#9C27B0', width=2)
        
        self.radius_curve = self.radius_plot.plot([], [], pen=pen_radius)
        self.temp_curve = self.temp_plot.plot([], [], pen=pen_temp, name="T")
        self.superheat_curve = self.temp_plot.plot([], [], pen=pen_superheat, name="ΔT")
        self.evap_curve = self.evap_plot.plot([], [], pen=pen_evap)
        self.psat_curve = self.pressure_plot.plot([], [], pen=pen_psat, name="p_sat")
        self.pamb_line = None  # Will be added as infinite line
        
        # Time marker lines (vertical lines showing current playback position)
        self._time_markers = []
        
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
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
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
        self._result = result
        
        # Update curves
        self.radius_curve.setData(result.t, result.R_mm)
        self.temp_curve.setData(result.t, result.T)
        self.superheat_curve.setData(result.t, result.superheat + 273.15)  # Offset for visibility
        self.evap_curve.setData(result.t, result.m_dot)
        self.psat_curve.setData(result.t, result.p_sat)
        
        # Add/update ambient pressure reference line
        if self.pamb_line is not None:
            self.pressure_plot.removeItem(self.pamb_line)
        self.pamb_line = pg.InfiniteLine(
            pos=p_ambient,
            angle=0,
            pen=pg.mkPen(color='#FF9800', width=2, style=Qt.PenStyle.DashLine),
            label=f'p_amb = {p_ambient:.0f} Pa',
            labelOpts={'position': 0.1, 'color': '#FF9800'}
        )
        self.pressure_plot.addItem(self.pamb_line)
        
        # Clear old time markers
        self._clear_time_markers()
        
        # Auto-range plots
        self.radius_plot.autoRange()
        self.temp_plot.autoRange()
        self.evap_plot.autoRange()
        self.pressure_plot.autoRange()
        
        # Update status with flash boiling info
        initial_superheat = result.superheat[0] if len(result.superheat) > 0 else 0
        
        if result.fragmented:
            status = f"💥 FRAGMENTATION at t = {result.fragmentation_time*1000:.2f} ms! Initial ΔT = {initial_superheat:.1f} K"
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffcccc; border-radius: 3px; font-weight: bold;")
        elif result.evaporation_complete:
            status = f"✓ Complete evaporation at t = {result.t[-1]*1000:.2f} ms (Initial ΔT = {initial_superheat:.1f} K)"
            self.status_label.setStyleSheet("padding: 5px; background-color: #ccffcc; border-radius: 3px;")
        elif result.T[-1] <= 273.15:
            status = f"❄ Freezing at t = {result.t[-1]*1000:.2f} ms, T = {result.T[-1]:.1f} K"
            self.status_label.setStyleSheet("padding: 5px; background-color: #cce5ff; border-radius: 3px;")
        else:
            status = f"t = {result.t[-1]*1000:.2f} ms | R = {result.R_mm[-1]:.3f} mm | ΔT = {result.superheat[-1]:.1f} K"
            self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        
        self.status_label.setText(status)
    
    def set_time_marker(self, t: float):
        """
        Set vertical time marker on all plots.
        
        Parameters
        ----------
        t : float
            Time position for the marker
        """
        self._clear_time_markers()
        
        pen = pg.mkPen(color='#E91E63', width=2)
        
        for plot in [self.radius_plot, self.temp_plot, self.evap_plot, self.pressure_plot]:
            marker = pg.InfiniteLine(pos=t, angle=90, pen=pen)
            plot.addItem(marker)
            self._time_markers.append((plot, marker))
    
    def _clear_time_markers(self):
        """Remove all time markers from plots."""
        for plot, marker in self._time_markers:
            plot.removeItem(marker)
        self._time_markers = []
    
    def clear_plots(self):
        """Clear all plot data."""
        self._result = None
        self.radius_curve.setData([], [])
        self.temp_curve.setData([], [])
        self.superheat_curve.setData([], [])
        self.evap_curve.setData([], [])
        self.psat_curve.setData([], [])
        self._clear_time_markers()
        if self.pamb_line is not None:
            self.pressure_plot.removeItem(self.pamb_line)
            self.pamb_line = None
        self.status_label.setText("Ready - adjust parameters and run simulation")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
