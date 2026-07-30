"""Range and Doppler processing."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr
from scipy.signal import get_window

from pyradarsystems.constants import SPEED_OF_LIGHT_MPS
from pyradarsystems.waveforms import FMCWWaveform


def _window(name: str | None, length: int) -> np.ndarray:
    if name is None or name.lower() in {"none", "rect", "rectangular", "boxcar"}:
        return np.ones(length)
    return get_window(name, length, fftbins=True)


@dataclass(frozen=True)
class RangeDopplerProcessor:
    range_window: str | None = "hann"
    doppler_window: str | None = "hann"
    range_fft_size: int | None = None
    doppler_fft_size: int | None = None
    remove_mean_slow_time: bool = False
    normalize_windows: bool = True

    def process(self, raw: xr.DataArray, waveform: FMCWWaveform) -> xr.DataArray:
        expected = ("frame", "tx", "rx", "chirp", "sample")
        if tuple(raw.dims) != expected:
            raise ValueError(f"raw cube dims must be {expected}, got {raw.dims}")
        values = np.asarray(raw.values)
        num_frames, num_tx, num_rx, num_chirps, num_samples = values.shape
        n_range = self.range_fft_size or num_samples
        n_doppler = self.doppler_fft_size or num_chirps
        if n_range < num_samples or n_doppler < num_chirps:
            raise ValueError("FFT sizes cannot be smaller than input dimensions")

        rw = _window(self.range_window, num_samples)
        dw = _window(self.doppler_window, num_chirps)
        if self.normalize_windows:
            rw = rw / np.sqrt(np.mean(rw**2))
            dw = dw / np.sqrt(np.mean(dw**2))

        ranged = np.fft.fft(values * rw.reshape(1, 1, 1, 1, -1), n=n_range, axis=-1)
        ranged = ranged[..., : n_range // 2]
        if self.remove_mean_slow_time:
            ranged = ranged - ranged.mean(axis=-2, keepdims=True)
        ranged *= dw.reshape(1, 1, 1, -1, 1)
        rd = np.fft.fftshift(np.fft.fft(ranged, n=n_doppler, axis=-2), axes=-2)

        range_frequency = np.fft.fftfreq(n_range, d=1.0 / waveform.sampling_rate_hz)[: n_range // 2]
        range_axis = SPEED_OF_LIGHT_MPS * range_frequency / (2.0 * waveform.slope_hz_per_s)
        slow_time_interval = waveform.tx_slow_time_interval_s(num_tx)
        doppler_frequency = np.fft.fftshift(np.fft.fftfreq(n_doppler, d=slow_time_interval))
        velocity_axis = doppler_frequency * waveform.wavelength_m / 2.0

        attrs = dict(raw.attrs)
        attrs.update(
            {
                "long_name": "range-Doppler cube",
                "range_window": str(self.range_window),
                "doppler_window": str(self.doppler_window),
                "range_fft_size": n_range,
                "doppler_fft_size": n_doppler,
                "range_units": "m",
                "velocity_units": "m/s",
                "doppler_frequency_hz": doppler_frequency.tolist(),
            }
        )
        return xr.DataArray(
            rd,
            dims=("frame", "tx", "rx", "doppler", "range"),
            coords={
                "frame": raw.coords["frame"],
                "tx": raw.coords["tx"],
                "rx": raw.coords["rx"],
                "doppler": velocity_axis,
                "range": range_axis,
            },
            attrs=attrs,
            name="range_doppler",
        )


def nearest_bin(cube: xr.DataArray, *, range_m: float, velocity_mps: float) -> tuple[int, int]:
    range_index = int(np.argmin(np.abs(cube.coords["range"].values - range_m)))
    doppler_index = int(np.argmin(np.abs(cube.coords["doppler"].values - velocity_mps)))
    return doppler_index, range_index
