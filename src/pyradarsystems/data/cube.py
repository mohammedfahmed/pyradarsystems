"""Labelled radar-cube helpers."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import xarray as xr

RAW_DIMS = ("frame", "tx", "rx", "chirp", "sample")
RD_DIMS = ("frame", "tx", "rx", "doppler", "range")


def save_cube_npz(cube: xr.DataArray, path: str | Path) -> None:
    """Save a DataArray without requiring NetCDF complex-number support."""
    path = Path(path)
    payload: dict[str, np.ndarray | str] = {
        "data": np.asarray(cube.values),
        "dims": np.asarray(cube.dims),
        "name": cube.name or "radar_cube",
        "attrs_json": json.dumps(cube.attrs, sort_keys=True),
    }
    for dim in cube.dims:
        payload[f"coord_{dim}"] = np.asarray(cube.coords[dim].values)
    np.savez_compressed(path, **payload)


def load_cube_npz(path: str | Path) -> xr.DataArray:
    with np.load(path, allow_pickle=False) as data:
        dims = tuple(str(v) for v in data["dims"])
        coords = {dim: data[f"coord_{dim}"] for dim in dims}
        attrs = json.loads(str(data["attrs_json"]))
        return xr.DataArray(
            data["data"], dims=dims, coords=coords, attrs=attrs, name=str(data["name"])
        )
