"""Publication-oriented plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from pyradarsystems.metrics import normalize_db


def plot_range_doppler(
    rd_cube: xr.DataArray,
    path: str | Path,
    *,
    frame_index: int = 0,
    combine_channels: bool = True,
    dynamic_range_db: float = 60.0,
) -> None:
    values = np.asarray(rd_cube.isel(frame=frame_index).values)
    if combine_channels:
        power = np.sum(np.abs(values) ** 2, axis=(0, 1))
    else:
        power = np.abs(values[0, 0]) ** 2
    image = normalize_db(power, floor_db=-dynamic_range_db)
    fig, ax = plt.subplots(figsize=(8, 5))
    mesh = ax.pcolormesh(
        rd_cube.coords["range"].values,
        rd_cube.coords["doppler"].values,
        image,
        shading="auto",
    )
    fig.colorbar(mesh, ax=ax, label="Normalized power (dB)")
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Radial velocity (m/s)")
    ax.set_title("Range-Doppler map")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_angle_spectrum(
    azimuth_deg: np.ndarray,
    power: np.ndarray,
    path: str | Path,
    *,
    title: str = "Angle spectrum",
) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(azimuth_deg, normalize_db(power, floor_db=-60))
    ax.set_xlabel("Azimuth (deg)")
    ax.set_ylabel("Normalized power (dB)")
    ax.set_ylim(-60, 1)
    ax.grid(True)
    ax.set_title(title)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
