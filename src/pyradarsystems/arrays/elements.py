"""Element-pattern models used by simulation and array analysis.

The public convention is a normalized *one-way power gain*. A value of one is
boresight gain and zero is a perfect null. The radar simulator converts the TX
and RX power gains to the corresponding complex-voltage scaling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


class ElementPattern(ABC):
    """Abstract normalized one-way element power pattern."""

    @abstractmethod
    def power_gain(
        self,
        azimuth_deg: float | np.ndarray,
        elevation_deg: float | np.ndarray = 0.0,
    ) -> np.ndarray:
        """Return normalized one-way power gain."""

    @abstractmethod
    def as_dict(self) -> dict[str, Any]:
        """Return a serializable model description."""


@dataclass(frozen=True)
class IsotropicElementPattern(ElementPattern):
    """Unit gain in every direction."""

    def power_gain(
        self,
        azimuth_deg: float | np.ndarray,
        elevation_deg: float | np.ndarray = 0.0,
    ) -> np.ndarray:
        azimuth, elevation = np.broadcast_arrays(
            np.asarray(azimuth_deg, dtype=float),
            np.asarray(elevation_deg, dtype=float),
        )
        return np.ones(np.broadcast_shapes(azimuth.shape, elevation.shape), dtype=float)

    def as_dict(self) -> dict[str, Any]:
        return {"type": "isotropic"}


@dataclass(frozen=True)
class CosineElementPattern(ElementPattern):
    """Boresight cosine-power approximation.

    The boresight direction is +y, matching the package array convention. The
    off-boresight angle is therefore computed from the y component of the unit
    direction vector. ``exponent=2`` gives a ``cos(theta)^2`` one-way power
    pattern. With ``back_baffle=True``, the rear hemisphere is suppressed.
    """

    exponent: float = 2.0
    back_baffle: bool = True
    floor_power_gain: float = 0.0

    def __post_init__(self) -> None:
        if self.exponent < 0:
            raise ValueError("exponent cannot be negative")
        if not 0.0 <= self.floor_power_gain <= 1.0:
            raise ValueError("floor_power_gain must be between 0 and 1")

    def power_gain(
        self,
        azimuth_deg: float | np.ndarray,
        elevation_deg: float | np.ndarray = 0.0,
    ) -> np.ndarray:
        azimuth = np.deg2rad(np.asarray(azimuth_deg, dtype=float))
        elevation = np.deg2rad(np.asarray(elevation_deg, dtype=float))
        azimuth, elevation = np.broadcast_arrays(azimuth, elevation)
        boresight_cosine = np.cos(elevation) * np.cos(azimuth)
        if self.back_baffle:
            boresight_cosine = np.maximum(boresight_cosine, 0.0)
        else:
            boresight_cosine = np.abs(boresight_cosine)
        gain = boresight_cosine**self.exponent
        return np.maximum(gain, self.floor_power_gain)

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "cosine",
            "exponent": float(self.exponent),
            "back_baffle": bool(self.back_baffle),
            "floor_power_gain": float(self.floor_power_gain),
        }


@dataclass(frozen=True)
class TabulatedAzimuthElementPattern(ElementPattern):
    """Interpolated azimuth cut for measured or electromagnetic-solver data.

    Values are normalized one-way power gains. Samples must be ordered by
    increasing azimuth. Outside the supplied angular interval, ``fill_gain`` is
    returned instead of extrapolating.
    """

    azimuth_deg: np.ndarray
    power_gain_samples: np.ndarray
    fill_gain: float = 0.0

    def __post_init__(self) -> None:
        angles = np.asarray(self.azimuth_deg, dtype=float)
        gains = np.asarray(self.power_gain_samples, dtype=float)
        if angles.ndim != 1 or gains.ndim != 1 or angles.size != gains.size:
            raise ValueError("azimuth_deg and power_gain_samples must be equal-length 1D arrays")
        if angles.size < 2:
            raise ValueError("at least two pattern samples are required")
        if np.any(np.diff(angles) <= 0):
            raise ValueError("azimuth_deg must be strictly increasing")
        if np.any(gains < 0):
            raise ValueError("power_gain_samples cannot be negative")
        if self.fill_gain < 0:
            raise ValueError("fill_gain cannot be negative")
        peak = float(np.max(gains))
        if peak <= 0:
            raise ValueError("power_gain_samples must contain a positive value")
        object.__setattr__(self, "azimuth_deg", angles)
        object.__setattr__(self, "power_gain_samples", gains / peak)

    @classmethod
    def from_db(
        cls,
        azimuth_deg: np.ndarray,
        power_gain_db: np.ndarray,
        *,
        fill_gain_db: float = -120.0,
    ) -> "TabulatedAzimuthElementPattern":
        gains = 10.0 ** (np.asarray(power_gain_db, dtype=float) / 10.0)
        fill = 10.0 ** (float(fill_gain_db) / 10.0)
        return cls(
            azimuth_deg=np.asarray(azimuth_deg, dtype=float),
            power_gain_samples=gains,
            fill_gain=fill,
        )

    def power_gain(
        self,
        azimuth_deg: float | np.ndarray,
        elevation_deg: float | np.ndarray = 0.0,
    ) -> np.ndarray:
        azimuth = np.asarray(azimuth_deg, dtype=float)
        elevation = np.asarray(elevation_deg, dtype=float)
        azimuth, elevation = np.broadcast_arrays(azimuth, elevation)
        interpolated = np.interp(
            azimuth.ravel(),
            self.azimuth_deg,
            self.power_gain_samples,
            left=self.fill_gain,
            right=self.fill_gain,
        ).reshape(azimuth.shape)
        # A one-dimensional cut does not claim an elevation model. Suppress
        # directions outside the visible +/-90 degree elevation hemisphere.
        return np.where(np.abs(elevation) <= 90.0, interpolated, self.fill_gain)

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "tabulated_azimuth",
            "azimuth_deg": self.azimuth_deg.tolist(),
            "power_gain_samples": self.power_gain_samples.tolist(),
            "fill_gain": float(self.fill_gain),
        }


def element_voltage_factor(
    pattern: ElementPattern,
    azimuth_deg: float | np.ndarray,
    elevation_deg: float | np.ndarray = 0.0,
    *,
    propagation_passes: int = 1,
) -> np.ndarray:
    """Convert one-way power gain to a voltage factor.

    One propagation pass uses ``sqrt(g)``. A monostatic two-way element factor
    with the same normalized TX/RX pattern uses ``g``.
    """

    if propagation_passes not in {1, 2}:
        raise ValueError("propagation_passes must be 1 or 2")
    gain = np.asarray(pattern.power_gain(azimuth_deg, elevation_deg), dtype=float)
    return np.maximum(gain, 0.0) ** (propagation_passes / 2.0)
