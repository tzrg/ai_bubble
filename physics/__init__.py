"""Physics module for flash evaporation simulation."""

from .properties import WaterProperties
from .model import FlashEvaporationModel

__all__ = ["WaterProperties", "FlashEvaporationModel"]
