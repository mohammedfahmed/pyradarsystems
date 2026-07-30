"""Configuration hashing and experiment manifests."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import xarray
import yaml


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def configuration_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def package_version() -> str:
    try:
        return version("pyradarsystems")
    except PackageNotFoundError:
        return "0.2.0+source"


def build_manifest(configuration: dict, seed: int | None) -> dict:
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_sha256": configuration_hash(configuration),
        "seed": seed,
        "software": {
            "pyradarsystems": package_version(),
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "xarray": xarray.__version__,
            "platform": platform.platform(),
        },
        "configuration": configuration,
    }


def write_manifest(path: str | Path, configuration: dict, seed: int | None) -> dict:
    manifest = build_manifest(configuration, seed)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(manifest, stream, sort_keys=False)
    return manifest
