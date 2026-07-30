"""Closed-form Cramér-Rao lower bounds for basic single-tone radar estimates."""

from __future__ import annotations

import numpy as np

from pyradarsystems.constants import SPEED_OF_LIGHT_MPS


def single_tone_frequency_variance_crlb_hz2(
    snr_linear: float,
    num_samples: int,
    sample_interval_s: float,
) -> float:
    """Frequency-estimation variance bound for one complex sinusoid.

    The model has unknown complex amplitude and white circular complex Gaussian
    noise. ``snr_linear`` is signal power divided by complex-noise power per
    sample. The frequency is measured in hertz.
    """

    if snr_linear <= 0:
        raise ValueError("snr_linear must be positive")
    if num_samples < 2:
        raise ValueError("num_samples must be at least 2")
    if sample_interval_s <= 0:
        raise ValueError("sample_interval_s must be positive")
    denominator = (
        (2.0 * np.pi * sample_interval_s) ** 2
        * snr_linear
        * num_samples
        * (num_samples**2 - 1)
    )
    return float(6.0 / denominator)


def fmcw_range_variance_crlb_m2(
    snr_linear: float,
    num_samples: int,
    sampling_rate_hz: float,
    chirp_slope_hz_per_s: float,
) -> float:
    """Map the beat-frequency CRLB to FMCW range variance."""

    if sampling_rate_hz <= 0:
        raise ValueError("sampling_rate_hz must be positive")
    if chirp_slope_hz_per_s <= 0:
        raise ValueError("chirp_slope_hz_per_s must be positive")
    frequency_variance = single_tone_frequency_variance_crlb_hz2(
        snr_linear,
        num_samples,
        1.0 / sampling_rate_hz,
    )
    scale = SPEED_OF_LIGHT_MPS / (2.0 * chirp_slope_hz_per_s)
    return float(scale**2 * frequency_variance)


def doppler_velocity_variance_crlb_m2ps2(
    snr_linear: float,
    num_chirps: int,
    slow_time_interval_s: float,
    wavelength_m: float,
) -> float:
    """Map the slow-time Doppler-frequency CRLB to radial-velocity variance."""

    if wavelength_m <= 0:
        raise ValueError("wavelength_m must be positive")
    frequency_variance = single_tone_frequency_variance_crlb_hz2(
        snr_linear,
        num_chirps,
        slow_time_interval_s,
    )
    return float((wavelength_m / 2.0) ** 2 * frequency_variance)
