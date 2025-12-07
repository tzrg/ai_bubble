# Flash Evaporation Droplet Simulation

A physically accurate simulation and visualization of **flash boiling** (explosive evaporation) of a liquid droplet in low-pressure environments.

## Features

- **True flash boiling physics**: Surface evaporation + internal nucleate boiling
- **Explosive fragmentation**: Droplet shatters at high superheat
- **Real-time visualization**: Animated droplet with temperature-based coloring
- **Interactive controls**: Adjust all physical parameters with immediate feedback
- **Live plots**: Radius, temperature, superheat, evaporation rate, and pressure vs time
- **Playback with time markers**: Scrub through simulation with synchronized plot indicators

## Installation

### Prerequisites: Python Setup (from scratch)

If you don't have Python installed, follow these steps:

#### 1. Install pyenv (Python version manager)

**Windows (PowerShell as Administrator):**
```powershell
# Install pyenv-win via PowerShell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

# Restart your terminal, then verify installation
pyenv --version
```

**macOS/Linux:**
```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to your shell config (~/.bashrc, ~/.zshrc, etc.)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Restart terminal or source config
source ~/.bashrc
```

#### 2. Install Python

```bash
# List available versions
pyenv install --list

# Install Python 3.11 (recommended)
pyenv install 3.11.9

# Set as global default (or use 'pyenv local 3.11.9' for this project only)
pyenv global 3.11.9

# Verify
python --version
```

#### 3. Create a Virtual Environment

```bash
# Navigate to project directory
cd path/to/AI-Blase

# Create virtual environment
python -m venv .venv

# Activate it
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Your prompt should now show (.venv)
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### Quick Install (if Python is already set up)

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Make sure your virtual environment is activated, then:
python main.py
```

## Physical Model

### What is Flash Boiling?

Flash boiling occurs when a liquid is suddenly exposed to a pressure below its saturation pressure. The liquid becomes **superheated** (T > T_sat at ambient pressure), causing:

1. **Surface evaporation** - molecules escape from the droplet surface
2. **Nucleate boiling** - bubbles form inside the droplet when superheat exceeds a threshold
3. **Fragmentation** - at very high superheat, rapid bubble growth shatters the droplet

### Governing Equations

**Superheat Degree:**
```
ΔT = T_droplet - T_sat(p_ambient)
```

**Surface Evaporation (Hertz-Knudsen):**
```
ṁ_surface = 4πR² · α · (p_sat - p_ambient) / √(2π·R_s·T)
```

**Nucleate Boiling** (when ΔT > threshold):
```
ṁ_nucleate ∝ mass · nucleation_factor · (ΔT - ΔT_threshold)²
```

**Energy Balance:**
```
m · cₚ · dT/dt = -ṁ_total · h_fg
```

**Fragmentation Criterion:**
```
If ΔT > ΔT_fragmentation → explosive breakup
```

### Thermodynamic Properties

- **Saturation pressure**: Antoine equation
- **Latent heat**: Watson correlation (temperature-dependent)
- **Density**: Temperature-dependent correlation

## Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| R₀ | Initial droplet radius | 1 mm | 0.1-10 mm |
| T₀ | Initial droplet temperature | 373 K | 300-450 K |
| p∞ | Ambient pressure | 1000 Pa | 100-101325 Pa |
| α | Evaporation coefficient | 0.5 | 0.01-1.0 |
| Nucleation Factor | Internal boiling intensity | 10 | 1-100 |
| Fragmentation ΔT | Superheat for explosion | 30 K | 10-100 K |

## Example Scenarios

### Mild Flash Evaporation
- T₀ = 350 K, p∞ = 10000 Pa → Low superheat, slow evaporation

### Violent Flash Boiling
- T₀ = 373 K, p∞ = 1000 Pa → High superheat (~66 K), rapid boiling

### Explosive Fragmentation
- T₀ = 400 K, p∞ = 500 Pa → Very high superheat, droplet shatters
