"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from pyradarsystems.arrays import RadarArray
from pyradarsystems.processing import AngleEstimator, RangeDopplerProcessor, extract_virtual_snapshot, nearest_bin
from pyradarsystems.reproducibility import write_manifest
from pyradarsystems.scene import PointTarget
from pyradarsystems.simulation import TDMFMCWSimulator
from pyradarsystems.system import RadarSystem
from pyradarsystems.visualization import plot_angle_spectrum, plot_range_doppler
from pyradarsystems.waveforms import FMCWWaveform


def run_demo(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    waveform = FMCWWaveform()
    array = RadarArray.ula(3, 4, waveform.wavelength_m)
    system = RadarSystem(waveform=waveform, array=array, tx_power_w=0.01)
    target = PointTarget(25.0, -3.0, 12.0, rcs_sqm=10.0)
    simulator = TDMFMCWSimulator(system, seed=7)
    raw = simulator.simulate([target])
    rd = RangeDopplerProcessor(range_fft_size=1024, doppler_fft_size=128).process(raw, waveform)
    di, ri = nearest_bin(rd, range_m=target.range_m, velocity_mps=target.radial_velocity_mps)
    snapshot = extract_virtual_snapshot(rd, array, waveform, frame_index=0, doppler_index=di, range_index=ri)
    grid = np.linspace(-60, 60, 1201)
    estimate, spectrum = AngleEstimator("bartlett").estimate(snapshot, array.virtual_positions_m, waveform.wavelength_m, grid)
    plot_range_doppler(rd, output / "range_doppler.png")
    plot_angle_spectrum(grid, spectrum, output / "angle_spectrum.png")
    summary = {
        "true_range_m": target.range_m,
        "estimated_range_m": float(rd.coords["range"].values[ri]),
        "true_velocity_mps": target.radial_velocity_mps,
        "estimated_velocity_mps": float(rd.coords["doppler"].values[di]),
        "true_azimuth_deg": target.azimuth_deg,
        "estimated_azimuth_deg": estimate,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_manifest(output / "manifest.yaml", {"system": system.as_dict(), "targets": [target.as_dict()]}, 7)
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="pyradar")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="Run the built-in 77-GHz point-target demo")
    demo.add_argument("--output", type=Path, default=Path("results/cli_demo"))
    args = parser.parse_args()
    if args.command == "demo":
        run_demo(args.output)
