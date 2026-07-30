"""FMCW waveform definitions and analytical properties."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from pyradarsystems.constants import SPEED_OF_LIGHT_MPS


@dataclass(frozen=True)
class FMCWWaveform:
    """Linear up-chirp FMCW waveform.

    Parameters use SI units. ``chirps_per_tx`` is the number of chirps emitted by
    each transmitter in one frame. For TDM-MIMO, the physical frame contains
    ``chirps_per_tx * num_tx`` chirp slots.
    """

    carrier_frequency_hz: float = 77e9
    bandwidth_hz: float = 1e9
    chirp_duration_s: float = 50e-6
    idle_time_s: float = 10e-6
    sampling_rate_hz: float = 10e6
    samples_per_chirp: int = 500
    chirps_per_tx: int = 64

    def __post_init__(self) -> None:
        positive = {
            "carrier_frequency_hz": self.carrier_frequency_hz,
            "bandwidth_hz": self.bandwidth_hz,
            "chirp_duration_s": self.chirp_duration_s,
            "sampling_rate_hz": self.sampling_rate_hz,
            "samples_per_chirp": self.samples_per_chirp,
            "chirps_per_tx": self.chirps_per_tx,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive, got {value!r}")
        if self.idle_time_s < 0:
            raise ValueError("idle_time_s cannot be negative")
        sampled_duration = self.samples_per_chirp / self.sampling_rate_hz
        if sampled_duration > self.chirp_duration_s * (1 + 1e-12):
            raise ValueError(
                "samples_per_chirp / sampling_rate_hz exceeds chirp_duration_s"
            )

    @property
    def wavelength_m(self) -> float:
        return SPEED_OF_LIGHT_MPS / self.carrier_frequency_hz

    @property
    def slope_hz_per_s(self) -> float:
        return self.bandwidth_hz / self.chirp_duration_s

    @property
    def chirp_repetition_interval_s(self) -> float:
        return self.chirp_duration_s + self.idle_time_s

    @property
    def range_resolution_m(self) -> float:
        return SPEED_OF_LIGHT_MPS / (2.0 * self.bandwidth_hz)

    @property
    def max_unambiguous_range_m(self) -> float:
        # Positive-frequency dechirped model, constrained by Nyquist beat frequency.
        return SPEED_OF_LIGHT_MPS * self.sampling_rate_hz / (4.0 * self.slope_hz_per_s)

    def tx_slow_time_interval_s(self, num_tx: int) -> float:
        if num_tx <= 0:
            raise ValueError("num_tx must be positive")
        return num_tx * self.chirp_repetition_interval_s

    def max_unambiguous_velocity_mps(self, num_tx: int) -> float:
        return self.wavelength_m / (4.0 * self.tx_slow_time_interval_s(num_tx))

    def velocity_resolution_mps(self, num_tx: int) -> float:
        coherent_time = self.chirps_per_tx * self.tx_slow_time_interval_s(num_tx)
        return self.wavelength_m / (2.0 * coherent_time)

    def beat_frequency_hz(self, range_m: float) -> float:
        return 2.0 * self.slope_hz_per_s * range_m / SPEED_OF_LIGHT_MPS

    def doppler_frequency_hz(self, radial_velocity_mps: float) -> float:
        return 2.0 * radial_velocity_mps / self.wavelength_m

    def fast_time_s(self) -> np.ndarray:
        return np.arange(self.samples_per_chirp, dtype=float) / self.sampling_rate_hz

    def chirp(self) -> np.ndarray:
        """Return one complex passband-equivalent linear chirp."""
        t = self.fast_time_s()
        phase = 2.0 * np.pi * (
            self.carrier_frequency_hz * t + 0.5 * self.slope_hz_per_s * t**2
        )
        return np.exp(1j * phase)

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)
