"""Stable component-specific seed derivation and seed manifests."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SeedRecord:
    trial_index: int
    stream: str
    seed: int

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


class SeedManager:
    """Derive deterministic seeds independent of execution order.

    Hash-based derivation avoids coupling seeds to worker count or scheduling.
    The same ``master_seed``, trial index, and stream name always produce the
    same unsigned 64-bit seed.
    """

    def __init__(self, master_seed: int) -> None:
        if not isinstance(master_seed, int):
            raise TypeError("master_seed must be an integer")
        if master_seed < 0:
            raise ValueError("master_seed cannot be negative")
        self.master_seed = master_seed

    def derive(self, trial_index: int, stream: str) -> int:
        if trial_index < 0:
            raise ValueError("trial_index cannot be negative")
        if not stream:
            raise ValueError("stream cannot be empty")
        payload = f"pyradarsystems:{self.master_seed}:{trial_index}:{stream}".encode()
        digest = hashlib.sha256(payload).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)

    def records(self, num_trials: int, streams: Iterable[str]) -> list[SeedRecord]:
        if num_trials <= 0:
            raise ValueError("num_trials must be positive")
        names = tuple(streams)
        if not names or any(not name for name in names):
            raise ValueError("streams must contain at least one non-empty name")
        if len(set(names)) != len(names):
            raise ValueError("stream names must be unique")
        return [
            SeedRecord(trial_index=trial, stream=stream, seed=self.derive(trial, stream))
            for trial in range(num_trials)
            for stream in names
        ]

    def write_csv(self, path: str | Path, num_trials: int, streams: Iterable[str]) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["trial_index", "stream", "seed"])
            writer.writeheader()
            writer.writerows(record.as_dict() for record in self.records(num_trials, streams))
        return destination
