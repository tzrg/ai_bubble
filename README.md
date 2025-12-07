# Flash Evaporation Droplet Simulation

A physically accurate simulation and visualization of flash evaporation of a liquid droplet.

## Features

- Real-time simulation of droplet evaporation using Hertz-Knudsen equation
- Interactive parameter controls (radius, temperature, pressure, evaporation coefficient)
- Live plots of droplet radius and temperature vs time
- Animated droplet visualization

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
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
