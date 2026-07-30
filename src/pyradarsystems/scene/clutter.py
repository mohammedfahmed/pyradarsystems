"""Simple distributed-clutter models built from transparent point scatterers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np

from .targets import PointTarget

RCSDistribution = Literal["equal", "exponential", "lognormal"]


@dataclass(frozen=True)
class AngularClutterModel:
    """Generate independent far-field clutter patches over range and azimuth.

    The model intentionally remains simple and inspectable. It is suitable for
    algorithm studies and aperture-taper comparisons, not a replacement for a
    terrain electromagnetic-scattering model.
    """

    num_patches: int
    range_min_m: float
    range_max_m: float
    azimuth_min_deg: float
    azimuth_max_deg: float
    total_rcs_sqm: float
    radial_velocity_mean_mps: float = 0.0
    radial_velocity_std_mps: float = 0.0
    elevation_deg: float = 0.0
    rcs_distribution: RCSDistribution = "exponential"
    lognormal_sigma_db: float = 4.0

    def __post_init__(self) -> None:
        if self.num_patches <= 0:
            raise ValueError("num_patches must be positive")
        if not 0 < self.range_min_m <= self.range_max_m:
            raise ValueError("range bounds must be positive and ordered")
        if self.azimuth_min_deg > self.azimuth_max_deg:
            raise ValueError("azimuth bounds must be ordered")
        if self.total_rcs_sqm < 0:
            raise ValueError("total_rcs_sqm cannot be negative")
        if self.radial_velocity_std_mps < 0:
            raise ValueError("radial_velocity_std_mps cannot be negative")
        if self.lognormal_sigma_db < 0:
            raise ValueError("lognormal_sigma_db cannot be negative")
        if self.rcs_distribution not in {"equal", "exponential", "lognormal"}:
            raise ValueError(f"unsupported rcs_distribution: {self.rcs_distribution}")

    def sample(self, seed: int | None = None) -> list[PointTarget]:
        rng = np.random.default_rng(seed)
        ranges = rng.uniform(self.range_min_m, self.range_max_m, self.num_patches)
        azimuths = rng.uniform(self.azimuth_min_deg, self.azimuth_max_deg, self.num_patches)
        velocities = rng.normal(
            self.radial_velocity_mean_mps,
            self.radial_velocity_std_mps,
            self.num_patches,
        )
        phases = rng.uniform(-np.pi, np.pi, self.num_patches)

        if self.rcs_distribution == "equal":
            relative_rcs = np.ones(self.num_patches)
        elif self.rcs_distribution == "exponential":
            relative_rcs = rng.exponential(scale=1.0, size=self.num_patches)
        else:
            sigma_natural = self.lognormal_sigma_db * np.log(10.0) / 10.0
            relative_rcs = rng.lognormal(mean=0.0, sigma=sigma_natural, size=self.num_patches)
        if self.total_rcs_sqm == 0:
            rcs = np.zeros(self.num_patches)
        else:
            rcs = relative_rcs / np.sum(relative_rcs) * self.total_rcs_sqm

        return [
            PointTarget(
                range_m=float(ranges[index]),
                radial_velocity_mps=float(velocities[index]),
                azimuth_deg=float(azimuths[index]),
                elevation_deg=float(self.elevation_deg),
                rcs_sqm=float(rcs[index]),
                initial_phase_rad=float(phases[index]),
            )
            for index in range(self.num_patches)
        ]

    def as_dict(self) -> dict[str, float | int | str]:
        return asdict(self)
