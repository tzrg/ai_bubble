# Flash Evaporation Droplet Simulation

A physically accurate simulation and visualization of flash evaporation of a liquid droplet.

## Features

- Real-time simulation of droplet evaporation using Hertz-Knudsen equation
- Interactive parameter controls (radius, temperature, pressure, evaporation coefficient)
- Live plots of droplet radius and temperature vs time
- Animated droplet visualization

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

The simulation solves coupled ODEs for:
- **Mass balance**: dR/dt based on evaporation mass flux
- **Energy balance**: dT/dt based on latent heat removal

Key equations:
- Hertz-Knudsen evaporation rate
- Antoine equation for saturation pressure
- Clausius-Clapeyron relation for latent heat variation

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| R₀ | Initial droplet radius | 1 mm |
| T₀ | Initial droplet temperature | 300 K |
| p∞ | Ambient pressure | 1000 Pa |
| α | Evaporation coefficient | 0.1 |
