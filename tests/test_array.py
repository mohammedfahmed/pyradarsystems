import numpy as np

from pyradarsystems import FMCWWaveform, RadarArray
from pyradarsystems.arrays import steering_vector


def test_broadside_steering_is_all_ones_for_x_axis_ula() -> None:
    waveform = FMCWWaveform()
    array = RadarArray.ula(1, 8, waveform.wavelength_m)
    vector = steering_vector(array.rx_positions_m, waveform.wavelength_m, 0.0)
    assert np.allclose(vector, 1.0 + 0.0j)


def test_virtual_element_count() -> None:
    waveform = FMCWWaveform()
    array = RadarArray.ula(3, 4, waveform.wavelength_m)
    assert array.virtual_positions_m.shape == (12, 3)
