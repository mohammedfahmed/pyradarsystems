"""Virtual-array formation and angle estimation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import xarray as xr

from pyradarsystems.arrays import RadarArray, steering_vector
from pyradarsystems.waveforms import FMCWWaveform


def extract_virtual_snapshot(
    rd_cube: xr.DataArray,
    array: RadarArray,
    waveform: FMCWWaveform,
    *,
    frame_index: int,
    doppler_index: int,
    range_index: int,
    compensate_tdm: bool = True,
) -> np.ndarray:
    """Extract TX-major, RX-minor virtual-array data from one RD cell."""
    sample = np.asarray(
        rd_cube.isel(frame=frame_index, doppler=doppler_index, range=range_index).values
    )
    if sample.shape != (array.num_tx, array.num_rx):
        raise ValueError("RD cube TX/RX dimensions do not match array")
    if compensate_tdm:
        velocity = float(rd_cube.coords["doppler"].values[doppler_index])
        fd = waveform.doppler_frequency_hz(velocity)
        offsets = np.arange(array.num_tx) * waveform.chirp_repetition_interval_s
        sample = sample * np.exp(-1j * 2.0 * np.pi * fd * offsets)[:, None]
    return sample.reshape(-1)


@dataclass(frozen=True)
class AngleEstimator:
    method: Literal["bartlett", "capon", "music"] = "bartlett"
    diagonal_loading: float = 1e-3

    def spectrum(
        self,
        snapshots: np.ndarray,
        positions_m: np.ndarray,
        wavelength_m: float,
        azimuth_grid_deg: np.ndarray,
        *,
        num_sources: int = 1,
    ) -> np.ndarray:
        x = np.asarray(snapshots, dtype=complex)
        if x.ndim == 1:
            x = x[:, None]
        if x.ndim != 2:
            raise ValueError("snapshots must have shape (elements,) or (elements, snapshots)")
        positions = np.asarray(positions_m, dtype=float)
        if positions.shape[0] != x.shape[0]:
            raise ValueError("positions and snapshots have different element counts")
        grid = np.asarray(azimuth_grid_deg, dtype=float)
        steering = np.column_stack(
            [steering_vector(positions, wavelength_m, angle) for angle in grid]
        )

        method = self.method.lower()
        if method == "bartlett":
            response = steering.conj().T @ x
            power = np.mean(np.abs(response) ** 2, axis=1) / x.shape[0] ** 2
        else:
            covariance = x @ x.conj().T / x.shape[1]
            loading = self.diagonal_loading * max(
                float(np.trace(covariance).real / x.shape[0]),
                np.finfo(float).eps,
            )
            covariance = covariance + loading * np.eye(x.shape[0])
            if method == "capon":
                inverse = np.linalg.pinv(covariance)
                denominator = np.einsum("gi,ij,gj->g", steering.T.conj(), inverse, steering.T).real
                power = 1.0 / np.maximum(denominator, np.finfo(float).eps)
            elif method == "music":
                if not 1 <= num_sources < x.shape[0]:
                    raise ValueError("num_sources must be between 1 and number of elements - 1")
                eigenvalues, eigenvectors = np.linalg.eigh(covariance)
                order = np.argsort(eigenvalues)
                noise_subspace = eigenvectors[:, order[: x.shape[0] - num_sources]]
                projection = noise_subspace @ noise_subspace.conj().T
                denominator = np.einsum(
                    "gi,ij,gj->g", steering.T.conj(), projection, steering.T
                ).real
                power = 1.0 / np.maximum(denominator, np.finfo(float).eps)
            else:
                raise ValueError(f"unsupported method: {self.method}")
        return np.asarray(power, dtype=float)

    def estimate(
        self,
        snapshots: np.ndarray,
        positions_m: np.ndarray,
        wavelength_m: float,
        azimuth_grid_deg: np.ndarray,
        *,
        num_sources: int = 1,
    ) -> tuple[float, np.ndarray]:
        power = self.spectrum(
            snapshots,
            positions_m,
            wavelength_m,
            azimuth_grid_deg,
            num_sources=num_sources,
        )
        angle = float(np.asarray(azimuth_grid_deg)[int(np.argmax(power))])
        return angle, power
