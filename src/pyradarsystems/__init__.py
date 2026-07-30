"""PyRadarSystems: validation-first radar simulation and processing framework.

Version 0.1 provides the 77-GHz FMCW TDM-MIMO core.
"""

from .arrays import RadarArray, direction_unit_vector, steering_vector
from .config import load_experiment_config
from .detection import ca_cfar_1d, ca_cfar_2d, ca_cfar_alpha
from .processing import AngleEstimator, RangeDopplerProcessor, extract_virtual_snapshot, nearest_bin
from .scene import PointTarget
from .simulation import SimulationImpairments, TDMFMCWSimulator
from .system import RadarSystem
from .waveforms import FMCWWaveform

__version__ = "0.1.0"

__all__ = [
    "FMCWWaveform",
    "RadarArray",
    "RadarSystem",
    "PointTarget",
    "SimulationImpairments",
    "TDMFMCWSimulator",
    "RangeDopplerProcessor",
    "AngleEstimator",
    "extract_virtual_snapshot",
    "nearest_bin",
    "steering_vector",
    "direction_unit_vector",
    "ca_cfar_1d",
    "ca_cfar_2d",
    "ca_cfar_alpha",
    "load_experiment_config",
]
