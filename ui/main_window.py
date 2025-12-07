"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from physics.model import FlashEvaporationModel, SimulationParameters, SimulationResult
from .controls import ParameterControlPanel
from .plots import SimulationPlots
from .droplet_view import DropletVisualization


class MainWindow(QMainWindow):
    """Main application window for flash evaporation simulation."""
    
    def __init__(self):
        super().__init__()
        
        self._result: SimulationResult = None
        self._setup_ui()
        self._setup_menu()
        
        # Run initial simulation
        QTimer.singleShot(100, self._run_simulation)
    
    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("Flash Evaporation Droplet Simulation")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout with splitter
        main_layout = QHBoxLayout(central)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Controls and droplet visualization
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Parameter controls
        self.controls = ParameterControlPanel()
        self.controls.runSimulation.connect(self._run_simulation)
        left_layout.addWidget(self.controls)
        
        # Droplet visualization
        self.droplet_view = DropletVisualization()
        left_layout.addWidget(self.droplet_view)
        
        left_panel.setMaximumWidth(400)
        splitter.addWidget(left_panel)
        
        # Right panel: Plots
        self.plots = SimulationPlots()
        splitter.addWidget(self.plots)
        
        # Set splitter sizes
        splitter.setSizes([350, 850])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        reset_action = QAction("&Reset Parameters", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._reset_parameters)
        file_menu.addAction(reset_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        physics_action = QAction("&Physics Model", self)
        physics_action.triggered.connect(self._show_physics_info)
        help_menu.addAction(physics_action)
    
    def _run_simulation(self):
        """Run the simulation with current parameters."""
        try:
            self.status_bar.showMessage("Running simulation...")
            
            # Get parameters from controls
            params = self.controls.get_parameters()
            
            # Create and run model
            model = FlashEvaporationModel(params)
            self._result = model.solve()
            
            # Update plots
            self.plots.update_plots(self._result, params.p_ambient)
            
            # Update droplet visualization
            self.droplet_view.set_result(self._result)
            
            self.status_bar.showMessage(
                f"Simulation complete: {len(self._result.t)} points, "
                f"t_final = {self._result.t[-1]:.3f} s"
            )
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            QMessageBox.warning(self, "Simulation Error", str(e))
    
    def _reset_parameters(self):
        """Reset parameters to defaults."""
        default_params = SimulationParameters()
        self.controls.set_parameters(default_params)
        self._run_simulation()
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Flash Evaporation Simulation",
            "<h3>Flash Evaporation Droplet Simulation</h3>"
            "<p>A physically accurate simulation of flash evaporation "
            "of a liquid droplet in low-pressure environments.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Hertz-Knudsen evaporation model</li>"
            "<li>Temperature-dependent thermodynamic properties</li>"
            "<li>Real-time parameter adjustment</li>"
            "<li>Animated droplet visualization</li>"
            "</ul>"
            "<p>© 2024</p>"
        )
    
    def _show_physics_info(self):
        """Show physics model information."""
        QMessageBox.information(
            self,
            "Physics Model",
            "<h3>Governing Equations</h3>"
            "<p><b>Mass Balance:</b><br>"
            "dR/dt = -ṁ / (4πR²ρ)</p>"
            "<p><b>Energy Balance:</b><br>"
            "m·cₚ·dT/dt = -ṁ·hfg + Q̇conv</p>"
            "<p><b>Hertz-Knudsen Evaporation:</b><br>"
            "ṁ = 4πR²·α·(psat - p∞) / √(2π·Rs·T)</p>"
            "<p><b>Antoine Equation (Saturation Pressure):</b><br>"
            "log₁₀(psat) = A - B/(C + T)</p>"
            "<h3>Parameters</h3>"
            "<ul>"
            "<li><b>R₀</b>: Initial droplet radius</li>"
            "<li><b>T₀</b>: Initial droplet temperature</li>"
            "<li><b>p∞</b>: Ambient pressure</li>"
            "<li><b>α</b>: Evaporation coefficient (0.01-1.0)</li>"
            "</ul>"
        )
