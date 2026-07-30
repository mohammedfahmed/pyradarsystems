"""Array-pattern calculation and publication-oriented pattern metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.integrate import trapezoid
from scipy.signal import find_peaks

from pyradarsystems.arrays.elements import (
    ElementPattern,
    IsotropicElementPattern,
    element_voltage_factor,
)
from pyradarsystems.arrays.geometry import steering_vector


@dataclass(frozen=True)
class PatternMetrics:
    peak_angle_deg: float
    half_power_beamwidth_deg: float
    first_null_beamwidth_deg: float
    peak_sidelobe_level_db: float
    integrated_sidelobe_ratio_db: float
    mainlobe_left_deg: float
    mainlobe_right_deg: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def array_pattern(
    weights: np.ndarray,
    positions_m: np.ndarray,
    wavelength_m: float,
    azimuth_grid_deg: np.ndarray,
    *,
    elevation_deg: float = 0.0,
    steer_azimuth_deg: float = 0.0,
    element_pattern: ElementPattern | None = None,
    propagation_passes: int = 1,
    normalize: bool = True,
) -> np.ndarray:
    """Return array response power on an azimuth grid.

    ``weights`` are taper coefficients before steering. The steering phase is
    added internally. ``propagation_passes=2`` applies the same normalized
    element pattern on transmit and receive, useful for monostatic pattern
    studies.
    """

    grid = np.asarray(azimuth_grid_deg, dtype=float)
    if grid.ndim != 1 or grid.size < 2:
        raise ValueError("azimuth_grid_deg must be a 1D array with at least two samples")
    aperture = np.asarray(weights, dtype=complex)
    positions = np.asarray(positions_m, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions_m must have shape (N, 3)")
    if aperture.shape != (positions.shape[0],):
        raise ValueError("weights length must match number of positions")
    if wavelength_m <= 0:
        raise ValueError("wavelength_m must be positive")
    if propagation_passes not in {1, 2}:
        raise ValueError("propagation_passes must be 1 or 2")

    steered_weights = aperture * steering_vector(
        positions, wavelength_m, steer_azimuth_deg, elevation_deg
    )
    azimuth_rad = np.deg2rad(grid)
    elevation_rad = np.deg2rad(float(elevation_deg))
    directions = np.column_stack(
        (
            np.cos(elevation_rad) * np.sin(azimuth_rad),
            np.cos(elevation_rad) * np.cos(azimuth_rad),
            np.full(grid.size, np.sin(elevation_rad)),
        )
    )
    phase = 2.0 * np.pi / wavelength_m * (positions @ directions.T)
    steering = np.exp(1j * phase)
    field = steered_weights.conj() @ steering
    pattern = element_pattern or IsotropicElementPattern()
    field *= element_voltage_factor(
        pattern,
        grid,
        elevation_deg,
        propagation_passes=propagation_passes,
    )
    power = np.abs(field) ** 2
    if normalize:
        peak = float(np.max(power))
        if peak > 0:
            power = power / peak
    return np.asarray(power, dtype=float)


def _crossing(
    grid: np.ndarray, values: np.ndarray, start: int, direction: int, level: float
) -> float:
    index = start
    while 0 <= index + direction < values.size:
        next_index = index + direction
        if (values[index] - level) * (values[next_index] - level) <= 0:
            x0, x1 = grid[index], grid[next_index]
            y0, y1 = values[index], values[next_index]
            if np.isclose(y0, y1):
                return float((x0 + x1) / 2.0)
            return float(x0 + (level - y0) * (x1 - x0) / (y1 - y0))
        index = next_index
    return float(grid[0] if direction < 0 else grid[-1])


def pattern_metrics(power: np.ndarray, azimuth_grid_deg: np.ndarray) -> PatternMetrics:
    """Compute HPBW, first-null beamwidth, PSLR, and ISLR.

    The mainlobe is bounded by the nearest local minima surrounding the global
    maximum. This makes the metric explicit and reproducible for broadside or
    steered beams on a dense one-dimensional grid.
    """

    values = np.asarray(power, dtype=float)
    grid = np.asarray(azimuth_grid_deg, dtype=float)
    if values.ndim != 1 or grid.ndim != 1 or values.shape != grid.shape:
        raise ValueError("power and azimuth_grid_deg must be equal-length 1D arrays")
    if values.size < 5 or np.any(np.diff(grid) <= 0):
        raise ValueError("grid must be strictly increasing and contain at least five samples")
    if np.any(values < 0) or not np.all(np.isfinite(values)):
        raise ValueError("power must be finite and non-negative")
    peak_index = int(np.argmax(values))
    peak = float(values[peak_index])
    if peak <= 0:
        raise ValueError("power must contain a positive value")
    normalized = values / peak

    minima, _ = find_peaks(-normalized)
    left_candidates = minima[minima < peak_index]
    right_candidates = minima[minima > peak_index]
    left_null = int(left_candidates[-1]) if left_candidates.size else 0
    right_null = int(right_candidates[0]) if right_candidates.size else values.size - 1

    left_half = _crossing(grid, normalized, peak_index, -1, 0.5)
    right_half = _crossing(grid, normalized, peak_index, +1, 0.5)

    sidelobe_mask = np.ones(values.size, dtype=bool)
    sidelobe_mask[left_null : right_null + 1] = False
    sidelobe_peak = float(np.max(normalized[sidelobe_mask])) if np.any(sidelobe_mask) else 0.0
    pslr_db = 10.0 * np.log10(max(sidelobe_peak, np.finfo(float).tiny))

    main_power = float(
        trapezoid(
            normalized[left_null : right_null + 1],
            grid[left_null : right_null + 1],
        )
    )
    side_power = float(
        trapezoid(normalized[: left_null + 1], grid[: left_null + 1])
        + trapezoid(normalized[right_null:], grid[right_null:])
    )
    islr_db = 10.0 * np.log10(
        max(side_power, np.finfo(float).tiny)
        / max(main_power, np.finfo(float).tiny)
    )

    return PatternMetrics(
        peak_angle_deg=float(grid[peak_index]),
        half_power_beamwidth_deg=float(right_half - left_half),
        first_null_beamwidth_deg=float(grid[right_null] - grid[left_null]),
        peak_sidelobe_level_db=float(pslr_db),
        integrated_sidelobe_ratio_db=float(islr_db),
        mainlobe_left_deg=float(grid[left_null]),
        mainlobe_right_deg=float(grid[right_null]),
    )
