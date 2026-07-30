import numpy as np

from pyradarsystems import (
    CosineElementPattern,
    FMCWWaveform,
    RadarArray,
    array_pattern,
    make_taper,
    normalize_taper,
    pattern_metrics,
)


def test_constant_total_power_normalization_matches_uniform_reference() -> None:
    weights = make_taper(16, "hann")
    normalized, report = normalize_taper(weights, "constant_total_power")
    assert np.isclose(np.sum(np.abs(normalized) ** 2), 16.0)
    assert np.isclose(report.output_total_power, 16.0)


def test_uniform_ula_pattern_metrics_match_reference_values() -> None:
    waveform = FMCWWaveform()
    array = RadarArray.ula(1, 16, waveform.wavelength_m, rx_spacing_lambda=0.5)
    grid = np.linspace(-90.0, 90.0, 7201)
    power = array_pattern(
        np.ones(16),
        array.rx_positions_m,
        waveform.wavelength_m,
        grid,
    )
    metrics = pattern_metrics(power, grid)
    assert abs(metrics.peak_angle_deg) <= 0.025
    assert np.isclose(metrics.half_power_beamwidth_deg, 6.36, atol=0.08)
    assert np.isclose(metrics.peak_sidelobe_level_db, -13.15, atol=0.15)


def test_cosine_element_pattern_is_normalized_at_broadside() -> None:
    pattern = CosineElementPattern(exponent=2.0)
    gains = pattern.power_gain(np.array([0.0, 60.0, 90.0]))
    assert np.allclose(gains[:2], [1.0, 0.25], atol=1e-12)
    assert gains[2] < 1e-20
