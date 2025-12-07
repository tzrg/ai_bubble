"""Dialog showing governing equations for flash evaporation."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor


class EquationsDialog(QDialog):
    """Dialog displaying the governing equations for flash evaporation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Governing Equations")
        self.setMinimumSize(500, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # Title
        title = QLabel("Flash Boiling Physics")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)
        
        # Introduction
        intro = QLabel(
            "Flash boiling occurs when a liquid droplet is suddenly exposed to a pressure "
            "below its saturation pressure. The liquid becomes <b>superheated</b>, causing "
            "rapid evaporation from the surface and internal nucleate boiling."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        content_layout.addWidget(intro)
        
        # Superheat section
        content_layout.addWidget(self._create_section(
            "1. Superheat Degree",
            "The driving force for flash evaporation:",
            "ΔT = T_droplet − T_sat(p_ambient)",
            "Where T_sat is the saturation temperature at ambient pressure (from inverse Antoine equation)."
        ))
        
        # Surface evaporation section
        content_layout.addWidget(self._create_section(
            "2. Surface Evaporation (Hertz-Knudsen)",
            "Mass flux from the droplet surface:",
            "ṁ_surface = 4πR² · α · (p_sat − p_∞) / √(2π·R_s·T)",
            "• R = droplet radius [m]\n"
            "• α = evaporation coefficient (0.01-1.0)\n"
            "• p_sat = saturation pressure at droplet temperature [Pa]\n"
            "• p_∞ = ambient pressure [Pa]\n"
            "• R_s = specific gas constant (461.5 J/kg·K for water)"
        ))
        
        # Nucleate boiling section
        content_layout.addWidget(self._create_section(
            "3. Nucleate Boiling",
            "Internal bubble formation when ΔT > threshold:",
            "ṁ_nucleate = f · m · (ΔT − ΔT_threshold)² / τ",
            "• f = nucleation factor (intensity multiplier)\n"
            "• m = droplet mass [kg]\n"
            "• τ = characteristic boiling time\n"
            "• Only active when ΔT > superheat threshold (~5 K)"
        ))
        
        # Energy balance section
        content_layout.addWidget(self._create_section(
            "4. Energy Balance",
            "Temperature change due to latent heat removal:",
            "m · cₚ · dT/dt = −ṁ_total · h_fg + Q̇_conv",
            "• cₚ = specific heat capacity (4186 J/kg·K)\n"
            "• h_fg = latent heat of vaporization [J/kg]\n"
            "• Q̇_conv = convective heat transfer (optional)"
        ))
        
        # Mass balance section
        content_layout.addWidget(self._create_section(
            "5. Mass Balance",
            "Radius change due to evaporation:",
            "dR/dt = −ṁ_total / (4πR²ρ)",
            "• ρ = liquid density (~1000 kg/m³ for water)"
        ))
        
        # Fragmentation section
        content_layout.addWidget(self._create_section(
            "6. Fragmentation Criterion",
            "Explosive breakup at high superheat:",
            "If ΔT > ΔT_fragmentation → droplet shatters",
            "At very high superheat, bubble growth is so rapid that internal pressure "
            "exceeds surface tension, causing the droplet to explosively fragment into "
            "many smaller droplets."
        ))
        
        # Thermodynamic properties section
        content_layout.addWidget(self._create_section(
            "7. Thermodynamic Properties",
            "Temperature-dependent correlations:",
            "p_sat: Antoine equation\n"
            "h_fg: Watson correlation\n"
            "ρ: Temperature-dependent fit",
            "<b>Antoine equation:</b>\n"
            "log₁₀(p_sat [mmHg]) = A − B/(C + T[°C])\n"
            "A=8.07, B=1730.6, C=233.4 (for water)\n\n"
            "<b>Watson correlation for latent heat:</b>\n"
            "h_fg(T) = h_fg,ref · ((1−T_r)/(1−T_r,ref))^0.38"
        ))
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _create_section(self, title: str, description: str, equation: str, details: str) -> QWidget:
        """Create a section widget with title, equation, and details."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1565c0;")
        section_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        section_layout.addWidget(desc_label)
        
        # Equation box
        eq_label = QLabel(equation)
        eq_label.setFont(QFont("Consolas", 11))
        eq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eq_label.setStyleSheet(
            "background-color: #fff3e0; "
            "padding: 10px; "
            "border: 1px solid #ffcc80; "
            "border-radius: 5px;"
        )
        eq_label.setTextFormat(Qt.TextFormat.PlainText)
        section_layout.addWidget(eq_label)
        
        # Details
        details_label = QLabel(details)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #555; font-size: 10px; padding-left: 10px;")
        details_label.setTextFormat(Qt.TextFormat.RichText)
        section_layout.addWidget(details_label)
        
        return section
