"""Cell-averaging CFAR detectors."""

from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d


def ca_cfar_alpha(num_training_cells: int, pfa: float) -> float:
    if num_training_cells <= 0:
        raise ValueError("num_training_cells must be positive")
    if not 0 < pfa < 1:
        raise ValueError("pfa must be between 0 and 1")
    return num_training_cells * (pfa ** (-1.0 / num_training_cells) - 1.0)


def ca_cfar_1d(
    power: np.ndarray,
    *,
    training_cells: int = 12,
    guard_cells: int = 4,
    pfa: float = 1e-5,
) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(power, dtype=float)
    if x.ndim != 1:
        raise ValueError("power must be one-dimensional")
    if training_cells <= 0 or guard_cells < 0:
        raise ValueError("invalid training/guard cell counts")
    half = training_cells + guard_cells
    kernel = np.ones(2 * half + 1, dtype=float)
    kernel[half - guard_cells : half + guard_cells + 1] = 0.0
    num_training = int(kernel.sum())
    noise_sum = np.convolve(x, kernel, mode="same")
    valid_count = np.convolve(np.ones_like(x), kernel, mode="same")
    noise = noise_sum / np.maximum(valid_count, 1)
    threshold = noise * ca_cfar_alpha(num_training, pfa)
    valid = valid_count == num_training
    detection = (x > threshold) & valid
    threshold[~valid] = np.nan
    return detection, threshold


def ca_cfar_2d(
    power: np.ndarray,
    *,
    training: tuple[int, int] = (8, 4),
    guard: tuple[int, int] = (2, 1),
    pfa: float = 1e-5,
) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(power, dtype=float)
    if x.ndim != 2:
        raise ValueError("power must be two-dimensional")
    tr, td = training
    gr, gd = guard
    if min(tr, td) <= 0 or min(gr, gd) < 0:
        raise ValueError("invalid training/guard cell counts")
    shape = (2 * (tr + gr) + 1, 2 * (td + gd) + 1)
    kernel = np.ones(shape, dtype=float)
    center_r, center_d = tr + gr, td + gd
    kernel[
        center_r - gr : center_r + gr + 1,
        center_d - gd : center_d + gd + 1,
    ] = 0.0
    num_training = int(kernel.sum())
    noise_sum = convolve2d(x, kernel, mode="same", boundary="fill", fillvalue=0.0)
    valid_count = convolve2d(
        np.ones_like(x), kernel, mode="same", boundary="fill", fillvalue=0.0
    )
    noise = noise_sum / np.maximum(valid_count, 1)
    threshold = noise * ca_cfar_alpha(num_training, pfa)
    valid = valid_count == num_training
    detection = (x > threshold) & valid
    threshold[~valid] = np.nan
    return detection, threshold
