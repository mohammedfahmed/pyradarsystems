"""Radar array geometry and steering-vector utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _positions(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError(f"{name} must have shape (N, 3), got {array.shape}")
    if array.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one element")
    return array


@dataclass(frozen=True)
class RadarArray:
    """Physical TX and RX element coordinates in metres."""

    tx_positions_m: np.ndarray
    rx_positions_m: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "tx_positions_m", _positions(self.tx_positions_m, "tx_positions_m"))
        object.__setattr__(self, "rx_positions_m", _positions(self.rx_positions_m, "rx_positions_m"))

    @property
    def num_tx(self) -> int:
        return int(self.tx_positions_m.shape[0])

    @property
    def num_rx(self) -> int:
        return int(self.rx_positions_m.shape[0])

    @property
    def num_virtual(self) -> int:
        return self.num_tx * self.num_rx

    @property
    def virtual_positions_m(self) -> np.ndarray:
        # Far-field monostatic MIMO phase centre: r_tx + r_rx.
        return (self.tx_positions_m[:, None, :] + self.rx_positions_m[None, :, :]).reshape(-1, 3)

    @classmethod
    def ula(
        cls,
        num_tx: int,
        num_rx: int,
        wavelength_m: float,
        tx_spacing_lambda: float = 2.0,
        rx_spacing_lambda: float = 0.5,
    ) -> "RadarArray":
        tx_x = np.arange(num_tx) * tx_spacing_lambda * wavelength_m
        rx_x = np.arange(num_rx) * rx_spacing_lambda * wavelength_m
        tx = np.column_stack((tx_x, np.zeros(num_tx), np.zeros(num_tx)))
        rx = np.column_stack((rx_x, np.zeros(num_rx), np.zeros(num_rx)))
        return cls(tx_positions_m=tx, rx_positions_m=rx)

    @classmethod
    def tdm_3tx_4rx(cls, wavelength_m: float) -> "RadarArray":
        """Conventional 3-TX/4-RX linear virtual-array example.

        TX spacing is 2 wavelengths and RX spacing is 0.5 wavelength, producing
        a contiguous 12-element virtual ULA with half-wavelength phase-centre spacing.
        """
        return cls.ula(3, 4, wavelength_m, tx_spacing_lambda=2.0, rx_spacing_lambda=0.5)

    def as_dict(self) -> dict[str, list[list[float]]]:
        return {
            "tx_positions_m": self.tx_positions_m.tolist(),
            "rx_positions_m": self.rx_positions_m.tolist(),
        }


def direction_unit_vector(azimuth_deg: float, elevation_deg: float = 0.0) -> np.ndarray:
    """Direction vector using broadside convention.

    Azimuth 0 degrees is array broadside (+y). Positive azimuth rotates toward
    +x. Elevation is positive toward +z.
    """
    az = np.deg2rad(azimuth_deg)
    el = np.deg2rad(elevation_deg)
    return np.array([
        np.cos(el) * np.sin(az),
        np.cos(el) * np.cos(az),
        np.sin(el),
    ])


def steering_vector(
    positions_m: np.ndarray,
    wavelength_m: float,
    azimuth_deg: float,
    elevation_deg: float = 0.0,
) -> np.ndarray:
    positions = _positions(positions_m, "positions_m")
    direction = direction_unit_vector(azimuth_deg, elevation_deg)
    phase = 2.0 * np.pi / wavelength_m * (positions @ direction)
    return np.exp(1j * phase)
