"""Array-pattern example using the public taper and pattern APIs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
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
from pyradarsystems.metrics import normalize_db


def main() -> None:
    output = Path("results/aperture_taper_comparison")
    output.mkdir(parents=True, exist_ok=True)
    waveform = FMCWWaveform()
    array = RadarArray.ula(1, 16, waveform.wavelength_m, rx_spacing_lambda=0.5)
    pattern = CosineElementPattern(exponent=2.0)
    grid = np.linspace(-90.0, 90.0, 7201)
    definitions = {
        "Uniform": ("uniform", {}),
        "Hann": ("hann", {}),
        "Taylor 30 dB": ("taylor", {"sidelobe_level_db": 30.0, "nbar": 4}),
    }

    rows = []
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, (kind, options) in definitions.items():
        weights, report = normalize_taper(
            make_taper(16, kind, **options),
            "constant_total_power",
        )
        power = array_pattern(
            weights,
            array.rx_positions_m,
            waveform.wavelength_m,
            grid,
            element_pattern=pattern,
        )
        metrics = pattern_metrics(power, grid)
        rows.append({"taper": label, **report.as_dict(), **metrics.as_dict()})
        ax.plot(grid, normalize_db(power, -60.0), label=label)

    ax.set_xlabel("Azimuth (deg)")
    ax.set_ylabel("Normalized power (dB)")
    ax.set_ylim(-60, 1)
    ax.set_xlim(-60, 60)
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "taper_patterns.png", dpi=180)
    fig.savefig(output / "taper_patterns.pdf")
    plt.close(fig)

    with (output / "taper_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
