"""Array-pattern example for uniform, Hann, and Taylor receive tapers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal.windows import taylor

from pyradarsystems import FMCWWaveform, RadarArray
from pyradarsystems.arrays import steering_vector
from pyradarsystems.metrics import normalize_db


def response(weights: np.ndarray, positions: np.ndarray, wavelength: float, grid: np.ndarray) -> np.ndarray:
    broadside = steering_vector(positions, wavelength, 0.0)
    weights = weights * broadside
    return np.asarray([
        np.abs(np.vdot(weights, steering_vector(positions, wavelength, angle))) ** 2
        for angle in grid
    ])


def main() -> None:
    output = Path("results/aperture_taper_comparison")
    output.mkdir(parents=True, exist_ok=True)
    waveform = FMCWWaveform()
    array = RadarArray.ula(1, 16, waveform.wavelength_m, rx_spacing_lambda=0.5)
    positions = array.rx_positions_m
    tapers = {
        "Uniform": np.ones(16),
        "Hann": np.hanning(16),
        "Taylor 30 dB": taylor(16, nbar=4, sll=30, norm=True),
    }
    grid = np.linspace(-90, 90, 3601)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, weights in tapers.items():
        weights = weights / np.linalg.norm(weights)  # constant total aperture power
        ax.plot(grid, normalize_db(response(weights, positions, waveform.wavelength_m, grid), -60), label=label)
    ax.set_xlabel("Azimuth (deg)")
    ax.set_ylabel("Normalized power (dB)")
    ax.set_ylim(-60, 1)
    ax.set_xlim(-60, 60)
    ax.grid(True)
    ax.legend()
    ax.set_title("Receive-aperture taper comparison")
    fig.tight_layout()
    fig.savefig(output / "taper_patterns.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
