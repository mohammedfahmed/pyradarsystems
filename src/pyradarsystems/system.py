"""Radar system-level configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from pyradarsystems.arrays import (
    ElementPattern,
    IsotropicElementPattern,
    NormalizationPolicy,
    RadarArray,
    normalize_taper,
)
from pyradarsystems.waveforms import FMCWWaveform


@dataclass(frozen=True)
class RadarSystem:
    waveform: FMCWWaveform
    array: RadarArray
    tx_power_w: float = 0.01
    tx_gain_linear: float = 1.0
    rx_gain_linear: float = 1.0
    receiver_noise_figure_db: float = 10.0
    receiver_temperature_k: float = 290.0
    system_loss_linear: float = 1.0
    tx_taper: np.ndarray | None = field(default=None, repr=False)
    rx_taper: np.ndarray | None = field(default=None, repr=False)
    tx_taper_normalization: NormalizationPolicy = "none"
    rx_taper_normalization: NormalizationPolicy = "none"
    tx_element_pattern: ElementPattern = field(default_factory=IsotropicElementPattern)
    rx_element_pattern: ElementPattern = field(default_factory=IsotropicElementPattern)

    def __post_init__(self) -> None:
        if self.tx_power_w < 0:
            raise ValueError("tx_power_w cannot be negative")
        for name in ("tx_gain_linear", "rx_gain_linear", "system_loss_linear"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.receiver_temperature_k <= 0:
            raise ValueError("receiver_temperature_k must be positive")

        tx = (
            np.ones(self.array.num_tx, dtype=complex)
            if self.tx_taper is None
            else np.asarray(self.tx_taper, dtype=complex)
        )
        rx = (
            np.ones(self.array.num_rx, dtype=complex)
            if self.rx_taper is None
            else np.asarray(self.rx_taper, dtype=complex)
        )
        if tx.shape != (self.array.num_tx,):
            raise ValueError("tx_taper length must equal number of TX elements")
        if rx.shape != (self.array.num_rx,):
            raise ValueError("rx_taper length must equal number of RX elements")
        tx, _ = normalize_taper(tx, self.tx_taper_normalization)
        rx, _ = normalize_taper(rx, self.rx_taper_normalization)
        object.__setattr__(self, "tx_taper", tx)
        object.__setattr__(self, "rx_taper", rx)

        for name in ("tx_element_pattern", "rx_element_pattern"):
            pattern = getattr(self, name)
            if not isinstance(pattern, ElementPattern):
                raise TypeError(f"{name} must implement ElementPattern")

    @property
    def noise_figure_linear(self) -> float:
        return 10.0 ** (self.receiver_noise_figure_db / 10.0)

    def as_dict(self) -> dict:
        return {
            "waveform": self.waveform.as_dict(),
            "array": self.array.as_dict(),
            "tx_power_w": float(self.tx_power_w),
            "tx_gain_linear": float(self.tx_gain_linear),
            "rx_gain_linear": float(self.rx_gain_linear),
            "receiver_noise_figure_db": float(self.receiver_noise_figure_db),
            "receiver_temperature_k": float(self.receiver_temperature_k),
            "system_loss_linear": float(self.system_loss_linear),
            "tx_taper": [[float(v.real), float(v.imag)] for v in self.tx_taper],
            "rx_taper": [[float(v.real), float(v.imag)] for v in self.rx_taper],
            "tx_taper_normalization": self.tx_taper_normalization,
            "rx_taper_normalization": self.rx_taper_normalization,
            "tx_element_pattern": self.tx_element_pattern.as_dict(),
            "rx_element_pattern": self.rx_element_pattern.as_dict(),
        }
