"""Deterministic Monte Carlo execution and publication-ready result bundles."""

from __future__ import annotations

import csv
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import yaml

from pyradarsystems.experiments.reporting import write_latex_table
from pyradarsystems.experiments.seeds import SeedManager
from pyradarsystems.experiments.statistics import mean_confidence_interval
from pyradarsystems.reproducibility import build_manifest

MetricValue = float | int | bool
Evaluator = Callable[["TrialContext"], Mapping[str, MetricValue]]


@dataclass(frozen=True)
class TrialContext:
    trial_index: int
    seeds: Mapping[str, int]

    def rng(self, stream: str) -> np.random.Generator:
        try:
            seed = self.seeds[stream]
        except KeyError as exc:
            raise KeyError(f"unknown random stream: {stream}") from exc
        return np.random.default_rng(seed)


def _run_one(evaluator: Evaluator, context: TrialContext) -> dict[str, MetricValue]:
    result = dict(evaluator(context))
    for key, value in result.items():
        if not isinstance(key, str) or not key:
            raise ValueError("metric names must be non-empty strings")
        if not isinstance(value, (bool, int, float, np.integer, np.floating)):
            raise TypeError(f"metric {key!r} must be a numeric scalar")
        if not np.isfinite(float(value)):
            raise ValueError(f"metric {key!r} must be finite")
    return {"trial_index": context.trial_index, **result}


@dataclass(frozen=True)
class ExperimentResult:
    name: str
    master_seed: int
    streams: tuple[str, ...]
    records: tuple[dict[str, MetricValue], ...]
    confidence: float = 0.95

    @property
    def num_trials(self) -> int:
        return len(self.records)

    def metric_names(self) -> list[str]:
        names: set[str] = set()
        for record in self.records:
            names.update(record.keys())
        names.discard("trial_index")
        return sorted(names)

    def summary(self) -> list[dict[str, float | int | str]]:
        rows: list[dict[str, float | int | str]] = []
        for metric in self.metric_names():
            values = np.asarray([float(record[metric]) for record in self.records], dtype=float)
            interval = mean_confidence_interval(values, confidence=self.confidence)
            rows.append({"metric": metric, **interval.as_dict()})
        return rows

    def paired_difference(self, minuend: str, subtrahend: str):
        """Return a confidence interval for paired trial differences."""

        available = set(self.metric_names())
        missing = {minuend, subtrahend} - available
        if missing:
            raise KeyError(f"unknown metrics: {sorted(missing)}")
        differences = np.asarray(
            [float(record[minuend]) - float(record[subtrahend]) for record in self.records]
        )
        return mean_confidence_interval(differences, confidence=self.confidence)

    def write_bundle(
        self,
        output_dir: str | Path,
        *,
        configuration: Mapping[str, Any] | None = None,
    ) -> Path:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        metric_names = self.metric_names()
        with (output / "raw_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["trial_index", *metric_names])
            writer.writeheader()
            for record in self.records:
                writer.writerow({key: record.get(key) for key in ["trial_index", *metric_names]})
        summary_rows = self.summary()
        with (output / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
        write_latex_table(
            output / "summary.tex",
            summary_rows,
            ["metric", "count", "mean", "standard_deviation", "lower", "upper"],
            headers={
                "metric": "Metric",
                "count": "N",
                "mean": "Mean",
                "standard_deviation": "Std.",
                "lower": "CI low",
                "upper": "CI high",
            },
        )
        SeedManager(self.master_seed).write_csv(
            output / "seed_manifest.csv", self.num_trials, self.streams
        )
        resolved_configuration = {
            "experiment_name": self.name,
            "num_trials": self.num_trials,
            "master_seed": self.master_seed,
            "streams": list(self.streams),
            "confidence": self.confidence,
            "user_configuration": dict(configuration or {}),
        }
        with (output / "resolved_configuration.yaml").open("w", encoding="utf-8") as handle:
            yaml.safe_dump(resolved_configuration, handle, sort_keys=False)
        manifest = build_manifest(resolved_configuration, self.master_seed)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return output


@dataclass(frozen=True)
class MonteCarloStudy:
    name: str
    num_trials: int
    master_seed: int = 0
    streams: Sequence[str] = ("scene", "noise")
    confidence: float = 0.95
    max_workers: int = 1

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.num_trials <= 0:
            raise ValueError("num_trials must be positive")
        if self.master_seed < 0:
            raise ValueError("master_seed cannot be negative")
        if not 0 < self.confidence < 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        names = tuple(self.streams)
        if not names or any(not name for name in names):
            raise ValueError("streams must contain non-empty names")
        if len(set(names)) != len(names):
            raise ValueError("stream names must be unique")
        object.__setattr__(self, "streams", names)

    def contexts(self) -> list[TrialContext]:
        manager = SeedManager(self.master_seed)
        return [
            TrialContext(
                trial_index=index,
                seeds={stream: manager.derive(index, stream) for stream in self.streams},
            )
            for index in range(self.num_trials)
        ]

    def run(self, evaluator: Evaluator) -> ExperimentResult:
        contexts = self.contexts()
        if self.max_workers == 1:
            records = [_run_one(evaluator, context) for context in contexts]
        else:
            # The evaluator must be importable/picklable for process execution.
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                records = list(executor.map(_run_one, [evaluator] * len(contexts), contexts))
        records.sort(key=lambda row: int(row["trial_index"]))
        return ExperimentResult(
            name=self.name,
            master_seed=self.master_seed,
            streams=tuple(self.streams),
            records=tuple(records),
            confidence=self.confidence,
        )
