"""Transparent dechirped-signal simulator for FMCW TDM-MIMO radar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import xarray as xr

from pyradarsystems.arrays import direction_unit_vector, element_voltage_factor
from pyradarsystems.constants import BOLTZMANN_J_PER_K
from pyradarsystems.reproducibility import configuration_hash, package_version
from pyradarsystems.scene import PointTarget
from pyradarsystems.system import RadarSystem


@dataclass(frozen=True)
class SimulationImpairments:
    """Optional sample-domain impairments.

    Gain and phase standard deviations are independently applied to physical TX
    and RX channels and remain fixed over the simulated data cube.
    """

    tx_gain_std_db: float = 0.0
    rx_gain_std_db: float = 0.0
    tx_phase_std_deg: float = 0.0
    rx_phase_std_deg: float = 0.0
    phase_noise_std_rad_per_sample: float = 0.0
    adc_bits: int | None = None
    adc_full_scale: float | None = None

    def __post_init__(self) -> None:
        for name in (
            "tx_gain_std_db",
            "rx_gain_std_db",
            "tx_phase_std_deg",
            "rx_phase_std_deg",
            "phase_noise_std_rad_per_sample",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.adc_bits is not None and self.adc_bits < 2:
            raise ValueError("adc_bits must be at least 2")
        if self.adc_full_scale is not None and self.adc_full_scale <= 0:
            raise ValueError("adc_full_scale must be positive")

    def as_dict(self) -> dict:
        return self.__dict__.copy()


class TDMFMCWSimulator:
    """Generate a labelled dechirped ADC cube for far-field point targets."""

    def __init__(
        self,
        system: RadarSystem,
        *,
        seed: int | None = 0,
        impairments: SimulationImpairments | None = None,
    ) -> None:
        self.system = system
        self.seed = seed
        self.impairments = impairments or SimulationImpairments()
        self.rng = np.random.default_rng(seed)

    def received_power_w(self, target: PointTarget) -> float:
        """Monostatic radar-equation received power before taper coefficients."""
        s = self.system
        wavelength = s.waveform.wavelength_m
        numerator = (
            s.tx_power_w
            * s.tx_gain_linear
            * s.rx_gain_linear
            * wavelength**2
            * target.rcs_sqm
        )
        denominator = (4.0 * np.pi) ** 3 * target.range_m**4 * s.system_loss_linear
        return numerator / denominator

    def noise_power_w(self) -> float:
        s = self.system
        # Complex baseband noise over the sampled receiver bandwidth.
        return (
            BOLTZMANN_J_PER_K
            * s.receiver_temperature_k
            * s.waveform.sampling_rate_hz
            * s.noise_figure_linear
        )

    def _channel_errors(self) -> tuple[np.ndarray, np.ndarray]:
        imp = self.impairments
        tx_gain_db = self.rng.normal(0.0, imp.tx_gain_std_db, self.system.array.num_tx)
        rx_gain_db = self.rng.normal(0.0, imp.rx_gain_std_db, self.system.array.num_rx)
        tx_phase = np.deg2rad(self.rng.normal(0.0, imp.tx_phase_std_deg, self.system.array.num_tx))
        rx_phase = np.deg2rad(self.rng.normal(0.0, imp.rx_phase_std_deg, self.system.array.num_rx))
        tx_error = 10.0 ** (tx_gain_db / 20.0) * np.exp(1j * tx_phase)
        rx_error = 10.0 ** (rx_gain_db / 20.0) * np.exp(1j * rx_phase)
        return tx_error, rx_error

    def simulate(
        self,
        targets: Sequence[PointTarget],
        *,
        num_frames: int = 1,
        add_noise: bool = True,
    ) -> xr.DataArray:
        if num_frames <= 0:
            raise ValueError("num_frames must be positive")
        targets = list(targets)
        w = self.system.waveform
        a = self.system.array
        shape = (num_frames, a.num_tx, a.num_rx, w.chirps_per_tx, w.samples_per_chirp)
        data = np.zeros(shape, dtype=np.complex128)

        fast_time = w.fast_time_s()
        tx_error, rx_error = self._channel_errors()
        tx_cycle = w.tx_slow_time_interval_s(a.num_tx)
        frame_duration = w.chirps_per_tx * tx_cycle

        for frame_idx in range(num_frames):
            frame_offset = frame_idx * frame_duration
            for tx_idx in range(a.num_tx):
                tx_slot_offset = tx_idx * w.chirp_repetition_interval_s
                chirp_times = (
                    frame_offset
                    + tx_slot_offset
                    + np.arange(w.chirps_per_tx) * tx_cycle
                )
                for rx_idx in range(a.num_rx):
                    channel = data[frame_idx, tx_idx, rx_idx]
                    virtual_position = a.tx_positions_m[tx_idx] + a.rx_positions_m[rx_idx]
                    channel_scale = (
                        self.system.tx_taper[tx_idx]
                        * self.system.rx_taper[rx_idx]
                        * tx_error[tx_idx]
                        * rx_error[rx_idx]
                    )
                    for target in targets:
                        direction = direction_unit_vector(target.azimuth_deg, target.elevation_deg)
                        spatial_phase = (
                            2.0 * np.pi / w.wavelength_m * float(virtual_position @ direction)
                        )
                        beat_frequency = w.beat_frequency_hz(target.range_m)
                        doppler_frequency = w.doppler_frequency_hz(target.radial_velocity_mps)
                        tx_element_factor = element_voltage_factor(
                            self.system.tx_element_pattern,
                            target.azimuth_deg,
                            target.elevation_deg,
                            propagation_passes=1,
                        )
                        rx_element_factor = element_voltage_factor(
                            self.system.rx_element_pattern,
                            target.azimuth_deg,
                            target.elevation_deg,
                            propagation_passes=1,
                        )
                        amplitude = (
                            np.sqrt(self.received_power_w(target))
                            * channel_scale
                            * complex(np.asarray(tx_element_factor).item())
                            * complex(np.asarray(rx_element_factor).item())
                        )
                        phase_fast = 2.0 * np.pi * beat_frequency * fast_time
                        phase_slow = 2.0 * np.pi * doppler_frequency * chirp_times
                        channel += amplitude * np.exp(
                            1j
                            * (
                                phase_slow[:, None]
                                + phase_fast[None, :]
                                + spatial_phase
                                + target.initial_phase_rad
                            )
                        )

        if self.impairments.phase_noise_std_rad_per_sample > 0:
            increments = self.rng.normal(
                0.0, self.impairments.phase_noise_std_rad_per_sample, size=shape
            )
            phase_noise = np.cumsum(increments, axis=-1)
            data *= np.exp(1j * phase_noise)

        noise_power = self.noise_power_w()
        if add_noise and noise_power > 0:
            sigma = np.sqrt(noise_power / 2.0)
            data += sigma * (
                self.rng.standard_normal(shape) + 1j * self.rng.standard_normal(shape)
            )

        if self.impairments.adc_bits is not None:
            data = self._quantize(data)

        configuration = {
            "system": self.system.as_dict(),
            "targets": [target.as_dict() for target in targets],
            "impairments": self.impairments.as_dict(),
            "num_frames": num_frames,
            "add_noise": add_noise,
        }
        coords = {
            "frame": np.arange(num_frames),
            "tx": np.arange(a.num_tx),
            "rx": np.arange(a.num_rx),
            "chirp": np.arange(w.chirps_per_tx),
            "sample": np.arange(w.samples_per_chirp),
        }
        attrs = {
            "long_name": "dechirped TDM-MIMO radar cube",
            "units": "sqrt(W)",
            "carrier_frequency_hz": w.carrier_frequency_hz,
            "sampling_rate_hz": w.sampling_rate_hz,
            "chirp_repetition_interval_s": w.chirp_repetition_interval_s,
            "tx_slow_time_interval_s": tx_cycle,
            "coordinate_convention": "azimuth 0 deg is +y broadside; positive toward +x",
            "seed": -1 if self.seed is None else int(self.seed),
            "configuration_sha256": configuration_hash(configuration),
            "pyradarsystems_version": package_version(),
            "noise_power_w": float(noise_power if add_noise else 0.0),
        }
        return xr.DataArray(
            data,
            dims=("frame", "tx", "rx", "chirp", "sample"),
            coords=coords,
            attrs=attrs,
            name="adc",
        )

    def _quantize(self, data: np.ndarray) -> np.ndarray:
        bits = int(self.impairments.adc_bits or 0)
        full_scale = self.impairments.adc_full_scale
        if full_scale is None:
            peak = float(np.max(np.maximum(np.abs(data.real), np.abs(data.imag))))
            full_scale = max(peak, np.finfo(float).eps)
        levels = 2**bits
        step = 2.0 * full_scale / levels

        def quantize_component(value: np.ndarray) -> np.ndarray:
            clipped = np.clip(value, -full_scale, full_scale - step)
            return np.round(clipped / step) * step

        return quantize_component(data.real) + 1j * quantize_component(data.imag)
