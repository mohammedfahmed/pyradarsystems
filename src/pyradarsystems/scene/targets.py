"""Target definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PointTarget:
    range_m: float
    radial_velocity_mps: float = 0.0
    azimuth_deg: float = 0.0
    elevation_deg: float = 0.0
    rcs_sqm: float = 1.0
    initial_phase_rad: float = 0.0

    def __post_init__(self) -> None:
        if self.range_m <= 0:
            raise ValueError("range_m must be positive")
        if self.rcs_sqm < 0:
            raise ValueError("rcs_sqm cannot be negative")

    def as_dict(self) -> dict[str, float]:
        return asdict(self)
