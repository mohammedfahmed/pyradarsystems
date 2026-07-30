from pathlib import Path

import numpy as np

from pyradarsystems import MonteCarloStudy, SeedManager, mean_confidence_interval


def _normal_metric(context):
    return {"sample": float(context.rng("noise").normal())}


def test_seed_derivation_is_stable_and_stream_specific() -> None:
    manager = SeedManager(1234)
    assert manager.derive(7, "noise") == manager.derive(7, "noise")
    assert manager.derive(7, "noise") != manager.derive(7, "scene")
    assert manager.derive(7, "noise") != manager.derive(8, "noise")


def test_monte_carlo_results_are_reproducible_and_exportable(tmp_path: Path) -> None:
    study = MonteCarloStudy("normal", num_trials=20, master_seed=9, streams=("noise",))
    first = study.run(_normal_metric)
    second = study.run(_normal_metric)
    assert first.records == second.records
    output = first.write_bundle(tmp_path / "bundle", configuration={"distribution": "normal"})
    assert (output / "raw_metrics.csv").exists()
    assert (output / "summary.csv").exists()
    assert (output / "summary.tex").exists()
    assert (output / "seed_manifest.csv").exists()
    assert (output / "manifest.json").exists()


def test_confidence_interval_contains_sample_mean() -> None:
    values = np.arange(1.0, 11.0)
    interval = mean_confidence_interval(values)
    assert interval.lower < np.mean(values) < interval.upper
    assert interval.count == 10


def test_paired_difference_uses_matched_trials() -> None:
    def paired(context):
        noise = float(context.rng("noise").normal())
        return {"a": noise + 2.0, "b": noise}

    result = MonteCarloStudy("paired", 10, master_seed=4, streams=("noise",)).run(paired)
    interval = result.paired_difference("a", "b")
    assert np.isclose(interval.mean, 2.0)
    assert np.isclose(interval.standard_deviation, 0.0, atol=1e-15)
