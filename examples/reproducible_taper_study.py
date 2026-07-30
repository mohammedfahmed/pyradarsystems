"""Paired Monte Carlo taper study with deterministic seed manifests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pyradarsystems import (
    CosineElementPattern,
    FMCWWaveform,
    MonteCarloStudy,
    RadarArray,
    TrialContext,
    array_pattern,
    make_taper,
    normalize_taper,
    pattern_metrics,
)
from pyradarsystems.metrics import normalize_db


@dataclass(frozen=True)
class TaperEvaluator:
    positions_m: np.ndarray
    wavelength_m: float
    azimuth_grid_deg: np.ndarray
    gain_std_db: float = 0.25
    phase_std_deg: float = 2.0

    def __call__(self, context: TrialContext) -> dict[str, float]:
        rng = context.rng("calibration")
        gain_error = 10.0 ** (
            rng.normal(0.0, self.gain_std_db, self.positions_m.shape[0]) / 20.0
        )
        phase_error = np.exp(
            1j * np.deg2rad(rng.normal(0.0, self.phase_std_deg, self.positions_m.shape[0]))
        )
        channel_error = gain_error * phase_error
        result: dict[str, float] = {}
        definitions = {
            "uniform": make_taper(self.positions_m.shape[0], "uniform"),
            "hann": make_taper(self.positions_m.shape[0], "hann"),
            "taylor30": make_taper(
                self.positions_m.shape[0], "taylor", sidelobe_level_db=30.0, nbar=4
            ),
        }
        for name, taper in definitions.items():
            taper, _ = normalize_taper(taper, "constant_total_power")
            power = array_pattern(
                taper * channel_error,
                self.positions_m,
                self.wavelength_m,
                self.azimuth_grid_deg,
                element_pattern=CosineElementPattern(2.0),
            )
            metrics = pattern_metrics(power, self.azimuth_grid_deg)
            result[f"{name}.pslr_db"] = metrics.peak_sidelobe_level_db
            result[f"{name}.islr_db"] = metrics.integrated_sidelobe_ratio_db
            result[f"{name}.hpbw_deg"] = metrics.half_power_beamwidth_deg
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/reproducible_taper_study"))
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    waveform = FMCWWaveform()
    array = RadarArray.ula(1, 16, waveform.wavelength_m, rx_spacing_lambda=0.5)
    grid = np.linspace(-90.0, 90.0, 3601)
    evaluator = TaperEvaluator(array.rx_positions_m, waveform.wavelength_m, grid)
    study = MonteCarloStudy(
        name="paired_aperture_taper_calibration_study",
        num_trials=args.trials,
        master_seed=20260731,
        streams=("calibration",),
        max_workers=args.workers,
    )
    result = study.run(evaluator)
    result.write_bundle(
        args.output,
        configuration={
            "array_elements": 16,
            "spacing_lambda": 0.5,
            "normalization": "constant_total_power",
            "gain_std_db": evaluator.gain_std_db,
            "phase_std_deg": evaluator.phase_std_deg,
        },
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, kind, options in (
        ("Uniform", "uniform", {}),
        ("Hann", "hann", {}),
        ("Taylor 30 dB", "taylor", {"sidelobe_level_db": 30.0, "nbar": 4}),
    ):
        taper, _ = normalize_taper(
            make_taper(16, kind, **options), "constant_total_power"
        )
        power = array_pattern(
            taper,
            array.rx_positions_m,
            waveform.wavelength_m,
            grid,
            element_pattern=CosineElementPattern(2.0),
        )
        ax.plot(grid, normalize_db(power, -60.0), label=label)
    ax.set_xlabel("Azimuth (deg)")
    ax.set_ylabel("Normalized power (dB)")
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 1)
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output / "ideal_taper_patterns.png", dpi=180)
    fig.savefig(args.output / "ideal_taper_patterns.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
