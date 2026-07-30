"""YAML configuration loading for reproducible experiments."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from pyradarsystems.arrays import RadarArray
from pyradarsystems.scene import PointTarget
from pyradarsystems.simulation import SimulationImpairments
from pyradarsystems.system import RadarSystem
from pyradarsystems.waveforms import FMCWWaveform


def load_experiment_config(path: str | Path) -> tuple[RadarSystem, list[PointTarget], SimulationImpairments, dict]:
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
    system = RadarSystem(waveform=waveform, array=array, **system_cfg)
    targets = [PointTarget(**item) for item in raw.get("targets", [])]
    impairments = SimulationImpairments(**raw.get("impairments", {}))
    return system, targets, impairments, raw
