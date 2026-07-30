"""End-to-end single-target example with numerical verification."""

from __future__ import annotations

import json
from pathlib import Path

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
    nearest_bin,
)
from pyradarsystems.data import save_cube_npz
from pyradarsystems.reproducibility import write_manifest
from pyradarsystems.visualization import plot_angle_spectrum, plot_range_doppler


def main() -> None:
    output = Path("results/basic_point_target")
    output.mkdir(parents=True, exist_ok=True)

    waveform = FMCWWaveform(
        carrier_frequency_hz=77e9,
        bandwidth_hz=1e9,
        chirp_duration_s=50e-6,
        idle_time_s=10e-6,
        sampling_rate_hz=10e6,
        samples_per_chirp=500,
        chirps_per_tx=64,
    )
    array = RadarArray.ula(3, 4, waveform.wavelength_m)
    system = RadarSystem(
        waveform=waveform,
        array=array,
        tx_power_w=0.01,
        tx_gain_linear=10.0,
        rx_gain_linear=10.0,
        receiver_noise_figure_db=10.0,
    )
    target = PointTarget(
        range_m=25.0,
        radial_velocity_mps=-3.0,
        azimuth_deg=12.0,
        rcs_sqm=10.0,
    )
    seed = 7
    raw = TDMFMCWSimulator(system, seed=seed).simulate([target])
    rd = RangeDopplerProcessor(range_fft_size=1024, doppler_fft_size=128).process(raw, waveform)
    doppler_index, range_index = nearest_bin(
        rd, range_m=target.range_m, velocity_mps=target.radial_velocity_mps
    )
    snapshot = extract_virtual_snapshot(
        rd,
        array,
        waveform,
        frame_index=0,
        doppler_index=doppler_index,
        range_index=range_index,
    )
    grid = np.linspace(-60.0, 60.0, 1201)
    angle, spectrum = AngleEstimator("bartlett").estimate(
        snapshot, array.virtual_positions_m, waveform.wavelength_m, grid
    )

    summary = {
        "analytical_beat_frequency_hz": waveform.beat_frequency_hz(target.range_m),
        "range_resolution_m": waveform.range_resolution_m,
        "velocity_resolution_mps": waveform.velocity_resolution_mps(array.num_tx),
        "true_range_m": target.range_m,
        "estimated_range_m": float(rd.coords["range"].values[range_index]),
        "true_velocity_mps": target.radial_velocity_mps,
        "estimated_velocity_mps": float(rd.coords["doppler"].values[doppler_index]),
        "true_azimuth_deg": target.azimuth_deg,
        "estimated_azimuth_deg": angle,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    save_cube_npz(raw, output / "raw_cube.npz")
    plot_range_doppler(rd, output / "range_doppler.png")
    plot_angle_spectrum(grid, spectrum, output / "angle_spectrum.png")
    write_manifest(
        output / "manifest.yaml",
        {"system": system.as_dict(), "targets": [target.as_dict()]},
        seed,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
