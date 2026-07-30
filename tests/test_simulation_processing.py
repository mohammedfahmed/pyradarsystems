import numpy as np

from pyradarsystems import (
    AngleEstimator,
    FMCWWaveform,
    PointTarget,
    RadarArray,
    RadarSystem,
    RangeDopplerProcessor,
    TDMFMCWSimulator,
    extract_virtual_snapshot,
)


def test_single_target_estimates_are_within_bins() -> None:
    waveform = FMCWWaveform(
        bandwidth_hz=800e6,
        samples_per_chirp=256,
        sampling_rate_hz=8e6,
        chirp_duration_s=40e-6,
        idle_time_s=10e-6,
        chirps_per_tx=64,
    )
    array = RadarArray.ula(2, 4, waveform.wavelength_m, tx_spacing_lambda=2.0)
    system = RadarSystem(
        waveform, array, tx_power_w=1.0, tx_gain_linear=100.0, rx_gain_linear=100.0, receiver_noise_figure_db=0.0
    )
    target = PointTarget(20.0, 4.0, 15.0, rcs_sqm=100.0)
    raw = TDMFMCWSimulator(system, seed=2).simulate([target], add_noise=False)
    rd = RangeDopplerProcessor(range_window=None, doppler_window=None, range_fft_size=1024, doppler_fft_size=256).process(raw, waveform)
    combined = np.sum(np.abs(rd.values[0]) ** 2, axis=(0, 1))
    di, ri = np.unravel_index(np.argmax(combined), combined.shape)
    estimated_range = float(rd.coords["range"].values[ri])
    estimated_velocity = float(rd.coords["doppler"].values[di])
    range_bin = float(np.diff(rd.coords["range"].values[:2])[0])
    velocity_bin = float(np.diff(rd.coords["doppler"].values[:2])[0])
    assert abs(estimated_range - target.range_m) <= range_bin
    assert abs(estimated_velocity - target.radial_velocity_mps) <= abs(velocity_bin)

    snapshot = extract_virtual_snapshot(rd, array, waveform, frame_index=0, doppler_index=di, range_index=ri)
    grid = np.linspace(-40, 40, 1601)
    angle, _ = AngleEstimator("bartlett").estimate(snapshot, array.virtual_positions_m, waveform.wavelength_m, grid)
    assert abs(angle - target.azimuth_deg) <= 0.25
