"""Parameter control panel for simulation settings."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QDoubleSpinBox, QSlider, QPushButton, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from physics.model import SimulationParameters


class LabeledSlider(QWidget):
    """A slider with label showing current value."""
    
    valueChanged = pyqtSignal(float)
    
    def __init__(
        self,
        label: str,
        min_val: float,
        max_val: float,
        default: float,
        decimals: int = 2,
        unit: str = "",
        log_scale: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self.unit = unit
        self.log_scale = log_scale
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with label and value
        header = QHBoxLayout()
        self.label = QLabel(label)
        self.value_label = QLabel()
        header.addWidget(self.label)
        header.addStretch()
        header.addWidget(self.value_label)
        layout.addLayout(header)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
        # Set initial value
        self.set_value(default)
    
    def _slider_to_value(self, slider_val: int) -> float:
        """Convert slider position to actual value."""
        fraction = slider_val / 1000.0
        if self.log_scale:
            import math
            log_min = math.log10(self.min_val)
            log_max = math.log10(self.max_val)
            return 10 ** (log_min + fraction * (log_max - log_min))
        else:
            return self.min_val + fraction * (self.max_val - self.min_val)
    
    def _value_to_slider(self, value: float) -> int:
        """Convert actual value to slider position."""
        if self.log_scale:
            import math
            log_min = math.log10(self.min_val)
            log_max = math.log10(self.max_val)
            log_val = math.log10(max(value, self.min_val))
            fraction = (log_val - log_min) / (log_max - log_min)
        else:
            fraction = (value - self.min_val) / (self.max_val - self.min_val)
        return int(fraction * 1000)
    
    def _on_slider_changed(self, slider_val: int):
        """Handle slider value change."""
        value = self._slider_to_value(slider_val)
        self._update_value_label(value)
        self.valueChanged.emit(value)
    
    def _update_value_label(self, value: float):
        """Update the value display label."""
        if self.decimals == 0:
            text = f"{int(value)}"
        else:
            text = f"{value:.{self.decimals}f}"
        if self.unit:
            text += f" {self.unit}"
        self.value_label.setText(text)
    
    def value(self) -> float:
        """Get current value."""
        return self._slider_to_value(self.slider.value())
    
    def set_value(self, value: float):
        """Set current value."""
        self.slider.blockSignals(True)
        self.slider.setValue(self._value_to_slider(value))
        self.slider.blockSignals(False)
        self._update_value_label(value)


class ParameterControlPanel(QWidget):
    """Control panel for simulation parameters."""
    
    parametersChanged = pyqtSignal()
    runSimulation = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the control panel UI."""
        layout = QVBoxLayout(self)
        
        # Initial Conditions Group
        initial_group = QGroupBox("Initial Conditions")
        initial_layout = QVBoxLayout(initial_group)
        
        self.radius_slider = LabeledSlider(
            "Initial Radius (R₀)",
            min_val=0.1, max_val=10.0, default=1.0,
            decimals=2, unit="mm"
        )
        self.radius_slider.valueChanged.connect(self._on_parameter_changed)
        initial_layout.addWidget(self.radius_slider)
        
        self.temp_slider = LabeledSlider(
            "Initial Temperature (T₀)",
            min_val=280.0, max_val=373.0, default=300.0,
            decimals=1, unit="K"
        )
        self.temp_slider.valueChanged.connect(self._on_parameter_changed)
        initial_layout.addWidget(self.temp_slider)
        
        layout.addWidget(initial_group)
        
        # Ambient Conditions Group
        ambient_group = QGroupBox("Ambient Conditions")
        ambient_layout = QVBoxLayout(ambient_group)
        
        self.pressure_slider = LabeledSlider(
            "Ambient Pressure (p∞)",
            min_val=100.0, max_val=50000.0, default=1000.0,
            decimals=0, unit="Pa", log_scale=True
        )
        self.pressure_slider.valueChanged.connect(self._on_parameter_changed)
        ambient_layout.addWidget(self.pressure_slider)
        
        layout.addWidget(ambient_group)
        
        # Model Parameters Group
        model_group = QGroupBox("Model Parameters")
        model_layout = QVBoxLayout(model_group)
        
        self.alpha_slider = LabeledSlider(
            "Evaporation Coefficient (α)",
            min_val=0.01, max_val=1.0, default=0.1,
            decimals=3, log_scale=True
        )
        self.alpha_slider.valueChanged.connect(self._on_parameter_changed)
        model_layout.addWidget(self.alpha_slider)
        
        # Convection checkbox
        self.convection_check = QCheckBox("Include Convective Heat Transfer")
        self.convection_check.stateChanged.connect(self._on_parameter_changed)
        model_layout.addWidget(self.convection_check)
        
        layout.addWidget(model_group)
        
        # Simulation Settings Group
        sim_group = QGroupBox("Simulation Settings")
        sim_layout = QVBoxLayout(sim_group)
        
        self.time_slider = LabeledSlider(
            "Max Simulation Time",
            min_val=0.1, max_val=60.0, default=10.0,
            decimals=1, unit="s", log_scale=True
        )
        self.time_slider.valueChanged.connect(self._on_parameter_changed)
        sim_layout.addWidget(self.time_slider)
        
        layout.addWidget(sim_group)
        
        # Run Button
        self.run_button = QPushButton("Run Simulation")
        self.run_button.setMinimumHeight(40)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.run_button.clicked.connect(self.runSimulation.emit)
        layout.addWidget(self.run_button)
        
        # Auto-run checkbox
        self.auto_run_check = QCheckBox("Auto-run on parameter change")
        self.auto_run_check.setChecked(True)
        layout.addWidget(self.auto_run_check)
        
        layout.addStretch()
    
    def _on_parameter_changed(self):
        """Handle parameter change."""
        self.parametersChanged.emit()
        if self.auto_run_check.isChecked():
            self.runSimulation.emit()
    
    def get_parameters(self) -> SimulationParameters:
        """Get current simulation parameters."""
        return SimulationParameters(
            R0=self.radius_slider.value() * 1e-3,  # mm to m
            T0=self.temp_slider.value(),
            p_ambient=self.pressure_slider.value(),
            alpha=self.alpha_slider.value(),
            include_convection=self.convection_check.isChecked(),
            t_max=self.time_slider.value(),
            n_points=500
        )
    
    def set_parameters(self, params: SimulationParameters):
        """Set control values from parameters."""
        self.radius_slider.set_value(params.R0 * 1e3)  # m to mm
        self.temp_slider.set_value(params.T0)
        self.pressure_slider.set_value(params.p_ambient)
        self.alpha_slider.set_value(params.alpha)
        self.convection_check.setChecked(params.include_convection)
        self.time_slider.set_value(params.t_max)
