import numpy as np

from pyradarsystems import (
    AngularClutterModel,
    CosineElementPattern,
    FMCWWaveform,
    PointTarget,
    RadarArray,
    RadarSystem,
    TDMFMCWSimulator,
    doppler_velocity_variance_crlb_m2ps2,
    fmcw_range_variance_crlb_m2,
)


def test_clutter_sampling_is_deterministic_and_preserves_total_rcs() -> None:
    model = AngularClutterModel(
        num_patches=32,
        range_min_m=20.0,
        range_max_m=30.0,
        azimuth_min_deg=-50.0,
        azimuth_max_deg=50.0,
        total_rcs_sqm=80.0,
    )
    first = model.sample(seed=5)
    second = model.sample(seed=5)
    assert first == second
    assert np.isclose(sum(target.rcs_sqm for target in first), 80.0)


def test_tx_rx_element_patterns_scale_received_voltage() -> None:
    waveform = FMCWWaveform(
        samples_per_chirp=64,
        sampling_rate_hz=2e6,
        chirp_duration_s=32e-6,
        chirps_per_tx=4,
    )
    array = RadarArray.ula(1, 1, waveform.wavelength_m)
    target = PointTarget(5.0, azimuth_deg=60.0)
    isotropic = RadarSystem(waveform, array, tx_power_w=1.0)
    cosine = RadarSystem(
        waveform,
        array,
        tx_power_w=1.0,
        tx_element_pattern=CosineElementPattern(2.0),
        rx_element_pattern=CosineElementPattern(2.0),
    )
    reference = TDMFMCWSimulator(isotropic, seed=1).simulate([target], add_noise=False)
    directional = TDMFMCWSimulator(cosine, seed=1).simulate([target], add_noise=False)
    voltage_ratio = np.mean(np.abs(directional.values)) / np.mean(np.abs(reference.values))
    assert np.isclose(voltage_ratio, 0.25, atol=1e-12)


def test_crlb_improves_with_snr_and_sample_count() -> None:
    low_snr = fmcw_range_variance_crlb_m2(10.0, 64, 10e6, 20e12)
    high_snr = fmcw_range_variance_crlb_m2(100.0, 64, 10e6, 20e12)
    more_samples = fmcw_range_variance_crlb_m2(10.0, 128, 10e6, 20e12)
    assert high_snr < low_snr
    assert more_samples < low_snr
    velocity = doppler_velocity_variance_crlb_m2ps2(10.0, 64, 100e-6, 0.0039)
    assert velocity > 0
