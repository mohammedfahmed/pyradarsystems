"""Common radar and array metrics."""

from __future__ import annotations

import numpy as np


def db_power(value: np.ndarray | float, floor_db: float = -300.0) -> np.ndarray:
    x = np.asarray(value, dtype=float)
    return 10.0 * np.log10(np.maximum(x, 10.0 ** (floor_db / 10.0)))


def db_amplitude(value: np.ndarray | float, floor_db: float = -300.0) -> np.ndarray:
    x = np.asarray(value)
    return 20.0 * np.log10(np.maximum(np.abs(x), 10.0 ** (floor_db / 20.0)))


def normalize_db(power: np.ndarray, floor_db: float = -120.0) -> np.ndarray:
    x = np.asarray(power, dtype=float)
    peak = max(float(np.max(x)), np.finfo(float).eps)
    return np.maximum(db_power(x / peak), floor_db)
