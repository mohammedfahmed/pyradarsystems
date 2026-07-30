"""YAML configuration loading for reproducible experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from pyradarsystems.arrays import (
    CosineElementPattern,
    IsotropicElementPattern,
    RadarArray,
    TabulatedAzimuthElementPattern,
)
from pyradarsystems.scene import PointTarget
from pyradarsystems.simulation import SimulationImpairments
from pyradarsystems.system import RadarSystem
from pyradarsystems.waveforms import FMCWWaveform


def _element_pattern(config: dict[str, Any] | None):
    if not config:
        return IsotropicElementPattern()
    kind = str(config.get("type", "isotropic")).lower()
    if kind == "isotropic":
        return IsotropicElementPattern()
    if kind == "cosine":
        return CosineElementPattern(
            exponent=float(config.get("exponent", 2.0)),
            back_baffle=bool(config.get("back_baffle", True)),
            floor_power_gain=float(config.get("floor_power_gain", 0.0)),
        )
    if kind == "tabulated_azimuth":
        if "power_gain_db" in config:
            return TabulatedAzimuthElementPattern.from_db(
                np.asarray(config["azimuth_deg"], dtype=float),
                np.asarray(config["power_gain_db"], dtype=float),
                fill_gain_db=float(config.get("fill_gain_db", -120.0)),
            )
        return TabulatedAzimuthElementPattern(
            azimuth_deg=np.asarray(config["azimuth_deg"], dtype=float),
            power_gain_samples=np.asarray(config["power_gain_samples"], dtype=float),
            fill_gain=float(config.get("fill_gain", 0.0)),
        )
    raise ValueError(f"unsupported element pattern type: {kind}")


def load_experiment_config(
    path: str | Path,
) -> tuple[RadarSystem, list[PointTarget], SimulationImpairments, dict]:
    with Path(path).open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    waveform = FMCWWaveform(**raw["waveform"])
    array_cfg = raw["array"]
    if "tx_positions_m" in array_cfg:
        array = RadarArray(
            np.asarray(array_cfg["tx_positions_m"], dtype=float),
            np.asarray(array_cfg["rx_positions_m"], dtype=float),
        )
    else:
        array = RadarArray.ula(
            num_tx=int(array_cfg["num_tx"]),
            num_rx=int(array_cfg["num_rx"]),
            wavelength_m=waveform.wavelength_m,
            tx_spacing_lambda=float(array_cfg.get("tx_spacing_lambda", 2.0)),
            rx_spacing_lambda=float(array_cfg.get("rx_spacing_lambda", 0.5)),
        )
    system_cfg = dict(raw.get("system", {}))
    if "tx_taper" in system_cfg:
        system_cfg["tx_taper"] = np.asarray(system_cfg["tx_taper"], dtype=complex)
    if "rx_taper" in system_cfg:
        system_cfg["rx_taper"] = np.asarray(system_cfg["rx_taper"], dtype=complex)
    system_cfg["tx_element_pattern"] = _element_pattern(system_cfg.pop("tx_element_pattern", None))
    system_cfg["rx_element_pattern"] = _element_pattern(system_cfg.pop("rx_element_pattern", None))
    system = RadarSystem(waveform=waveform, array=array, **system_cfg)
    targets = [PointTarget(**item) for item in raw.get("targets", [])]
    impairments = SimulationImpairments(**raw.get("impairments", {}))
    return system, targets, impairments, raw
