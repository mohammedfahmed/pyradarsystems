import numpy as np

from pyradarsystems import FMCWWaveform
from pyradarsystems.constants import SPEED_OF_LIGHT_MPS


def test_range_resolution_and_beat_frequency() -> None:
    waveform = FMCWWaveform(bandwidth_hz=1e9, chirp_duration_s=50e-6)
    assert np.isclose(waveform.range_resolution_m, SPEED_OF_LIGHT_MPS / 2e9)
    expected = 2 * waveform.slope_hz_per_s * 35.0 / SPEED_OF_LIGHT_MPS
    assert np.isclose(waveform.beat_frequency_hz(35.0), expected)


def test_invalid_sampling_duration() -> None:
    import pytest

    with pytest.raises(ValueError):
        FMCWWaveform(chirp_duration_s=10e-6, sampling_rate_hz=1e6, samples_per_chirp=20)
