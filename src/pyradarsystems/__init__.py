"""PyRadarSystems: validation-first radar simulation and processing framework.

Version 0.2 adds the reproducible research experiment layer and paper-oriented
aperture-taper analysis to the 77-GHz FMCW TDM-MIMO core.
"""

from .arrays import (
    CosineElementPattern,
    ElementPattern,
    IsotropicElementPattern,
    PatternMetrics,
    RadarArray,
    TabulatedAzimuthElementPattern,
    TaperNormalizationReport,
    array_pattern,
    direction_unit_vector,
    make_taper,
    normalize_taper,
    pattern_metrics,
    steering_vector,
)
from .config import load_experiment_config
from .detection import ca_cfar_1d, ca_cfar_2d, ca_cfar_alpha
from .estimation import (
    doppler_velocity_variance_crlb_m2ps2,
    fmcw_range_variance_crlb_m2,
    single_tone_frequency_variance_crlb_hz2,
)
from .experiments import (
    ConfidenceInterval,
    ExperimentResult,
    MonteCarloStudy,
    SeedManager,
    SeedRecord,
    TrialContext,
    latex_escape,
    mean_confidence_interval,
    write_latex_table,
)
from .processing import AngleEstimator, RangeDopplerProcessor, extract_virtual_snapshot, nearest_bin
from .scene import AngularClutterModel, PointTarget
from .simulation import SimulationImpairments, TDMFMCWSimulator
from .system import RadarSystem
from .waveforms import FMCWWaveform

__version__ = "0.2.0"

__all__ = [
    "FMCWWaveform",
    "RadarArray",
    "RadarSystem",
    "PointTarget",
    "AngularClutterModel",
    "SimulationImpairments",
    "TDMFMCWSimulator",
    "RangeDopplerProcessor",
    "AngleEstimator",
    "extract_virtual_snapshot",
    "nearest_bin",
    "steering_vector",
    "direction_unit_vector",
    "ElementPattern",
    "IsotropicElementPattern",
    "CosineElementPattern",
    "TabulatedAzimuthElementPattern",
    "make_taper",
    "normalize_taper",
    "TaperNormalizationReport",
    "array_pattern",
    "pattern_metrics",
    "PatternMetrics",
    "ca_cfar_1d",
    "ca_cfar_2d",
    "ca_cfar_alpha",
    "SeedManager",
    "SeedRecord",
    "TrialContext",
    "MonteCarloStudy",
    "ExperimentResult",
    "ConfidenceInterval",
    "mean_confidence_interval",
    "latex_escape",
    "write_latex_table",
    "single_tone_frequency_variance_crlb_hz2",
    "fmcw_range_variance_crlb_m2",
    "doppler_velocity_variance_crlb_m2ps2",
    "load_experiment_config",
]
