"""Animated droplet visualization widget."""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QFont

from physics.model import SimulationResult


class DropletCanvas(QWidget):
    """Canvas widget for drawing the droplet."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        
        # Current state
        self.radius_fraction = 1.0  # 0 to 1
        self.temperature = 300.0  # K
        self.max_radius = 1.0  # mm (for scaling)
        
        # Colors
        self.cold_color = QColor(100, 149, 237)  # Cornflower blue
        self.hot_color = QColor(255, 99, 71)  # Tomato red
        
    def set_state(self, radius_mm: float, temperature: float, max_radius: float):
        """Update droplet state."""
        self.radius_fraction = radius_mm / max_radius if max_radius > 0 else 0
        self.temperature = temperature
        self.max_radius = max_radius
        self.update()
    
    def paintEvent(self, event):
        """Paint the droplet."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        w = self.width()
        h = self.height()
        center_x = w // 2
        center_y = h // 2
        
        # Calculate droplet size (max 80% of smaller dimension)
        max_pixel_radius = min(w, h) * 0.4
        pixel_radius = max(max_pixel_radius * self.radius_fraction, 2)
        
        # Calculate color based on temperature (273K = cold, 373K = hot)
        t_norm = (self.temperature - 273.0) / 100.0
        t_norm = max(0.0, min(1.0, t_norm))
        
        r = int(self.cold_color.red() + t_norm * (self.hot_color.red() - self.cold_color.red()))
        g = int(self.cold_color.green() + t_norm * (self.hot_color.green() - self.cold_color.green()))
        b = int(self.cold_color.blue() + t_norm * (self.hot_color.blue() - self.cold_color.blue()))
        droplet_color = QColor(r, g, b)
        
        # Create radial gradient for 3D effect
        gradient = QRadialGradient(
            center_x - pixel_radius * 0.3,
            center_y - pixel_radius * 0.3,
            pixel_radius * 1.5
        )
        highlight_color = droplet_color.lighter(150)
        gradient.setColorAt(0, highlight_color)
        gradient.setColorAt(0.5, droplet_color)
        gradient.setColorAt(1, droplet_color.darker(130))
        
        # Draw droplet
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(droplet_color.darker(120), 2))
        painter.drawEllipse(
            int(center_x - pixel_radius),
            int(center_y - pixel_radius),
            int(pixel_radius * 2),
            int(pixel_radius * 2)
        )
        
        # Draw evaporation particles if evaporating
        if self.radius_fraction < 0.99 and self.radius_fraction > 0.01:
            self._draw_vapor_particles(painter, center_x, center_y, pixel_radius)
        
        # Draw info text
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.setFont(QFont("Arial", 10))
        
        radius_mm = self.radius_fraction * self.max_radius
        info_text = f"R = {radius_mm:.3f} mm\nT = {self.temperature:.1f} K"
        painter.drawText(10, 20, info_text.split('\n')[0])
        painter.drawText(10, 35, info_text.split('\n')[1])
    
    def _draw_vapor_particles(self, painter, cx, cy, radius):
        """Draw vapor particles around the droplet."""
        import random
        random.seed(42)  # Consistent pattern
        
        painter.setPen(Qt.PenStyle.NoPen)
        vapor_color = QColor(200, 200, 255, 100)
        painter.setBrush(QBrush(vapor_color))
        
        n_particles = int(20 * (1 - self.radius_fraction))
        for i in range(n_particles):
            angle = random.uniform(0, 2 * np.pi)
            dist = radius + random.uniform(10, 40)
            px = cx + dist * np.cos(angle)
            py = cy + dist * np.sin(angle)
            size = random.uniform(3, 8)
            painter.drawEllipse(int(px - size/2), int(py - size/2), int(size), int(size))


class DropletVisualization(QWidget):
    """Widget for animated droplet visualization with time control."""
    
    timeChanged = pyqtSignal(float)
    helpRequested = pyqtSignal()  # Signal to show help dialog
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._current_index = 0
        self._playing = False
        self._timer_active = False
        
        self._setup_ui()
        
        # Animation timer - use singleShot for safer operation
        self._timer = QTimer(self)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._advance_frame)
    
    def _setup_ui(self):
        """Set up the visualization UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        
        # Title row with help button
        title_layout = QHBoxLayout()
        title = QLabel("Droplet Visualization")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_layout.addWidget(title)
        
        # Help button
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(24, 24)
        self.help_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.help_button.setToolTip("Show governing equations")
        self.help_button.clicked.connect(self.helpRequested.emit)
        title_layout.addWidget(self.help_button)
        layout.addLayout(title_layout)
        
        # Droplet canvas
        self.canvas = DropletCanvas()
        self.canvas.setMinimumSize(150, 150)
        layout.addWidget(self.canvas, stretch=1)
        
        # Time slider
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(5)
        self.time_label = QLabel("t = 0.000 s")
        self.time_label.setStyleSheet("font-size: 10px;")
        self.time_label.setMinimumWidth(80)
        
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(100)
        self.time_slider.valueChanged.connect(self._on_slider_changed)
        
        slider_layout.addWidget(self.time_label)
        slider_layout.addWidget(self.time_slider)
        layout.addLayout(slider_layout)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(3)
        
        self.play_button = QPushButton("▶")
        self.play_button.setFixedWidth(40)
        self.play_button.setToolTip("Play/Pause")
        self.play_button.clicked.connect(self._toggle_play)
        controls_layout.addWidget(self.play_button)
        
        self.reset_button = QPushButton("⟲")
        self.reset_button.setFixedWidth(40)
        self.reset_button.setToolTip("Reset to start")
        self.reset_button.clicked.connect(self._reset)
        controls_layout.addWidget(self.reset_button)
        
        # Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("font-size: 9px;")
        controls_layout.addWidget(speed_label)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(5)
        self.speed_slider.setMaximumWidth(60)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        controls_layout.addWidget(self.speed_slider)
        
        layout.addLayout(controls_layout)
    
    def set_result(self, result: SimulationResult):
        """Set simulation result for visualization."""
        # Stop any running animation first
        was_playing = self._playing
        if self._playing:
            self._stop_playback()
        
        self._result = result
        self._current_index = 0
        
        if result is not None and len(result.t) > 0:
            self.time_slider.blockSignals(True)
            self.time_slider.setMaximum(len(result.t) - 1)
            self.time_slider.setValue(0)
            self.time_slider.blockSignals(False)
            self._update_display()
    
    def _on_slider_changed(self, value: int):
        """Handle time slider change."""
        self._current_index = value
        self._update_display()
    
    def _update_display(self):
        """Update the droplet display for current time index."""
        if self._result is None or len(self._result.t) == 0:
            return
        
        idx = min(self._current_index, len(self._result.t) - 1)
        t = self._result.t[idx]
        R = self._result.R_mm[idx]
        T = self._result.T[idx]
        
        self.canvas.set_state(R, T, self._result.R_mm[0])
        self.time_label.setText(f"t = {t:.3f} s")
        self.timeChanged.emit(t)
    
    def _stop_playback(self):
        """Stop the animation playback."""
        if self._timer.isActive():
            self._timer.stop()
        self._playing = False
        self._timer_active = False
        self.play_button.setText("▶")
    
    def _on_speed_changed(self, value: int):
        """Handle speed slider change - update timer interval if playing."""
        if self._playing and self._timer.isActive():
            interval = max(16, 150 // value)  # 16ms minimum (~60fps max)
            self._timer.setInterval(interval)
    
    def _toggle_play(self):
        """Toggle animation playback."""
        if self._result is None or len(self._result.t) == 0:
            return
            
        if self._playing:
            self._stop_playback()
        else:
            # Calculate interval based on speed
            speed = self.speed_slider.value()
            interval = max(16, 150 // speed)  # 16ms minimum (~60fps max)
            self._timer.start(interval)
            self._playing = True
            self._timer_active = True
            self.play_button.setText("⏸")
    
    def _advance_frame(self):
        """Advance to next frame in animation."""
        if self._result is None or not self._playing:
            self._stop_playback()
            return
        
        if len(self._result.t) == 0:
            self._stop_playback()
            return
        
        self._current_index += 1
        if self._current_index >= len(self._result.t):
            self._current_index = 0
        
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(self._current_index)
        self.time_slider.blockSignals(False)
        self._update_display()
    
    def _reset(self):
        """Reset animation to start."""
        self._stop_playback()
        self._current_index = 0
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(0)
        self.time_slider.blockSignals(False)
        self._update_display()
