# Reproducible experiments

`MonteCarloStudy` separates the trial index from named random streams. Seeds are derived from the master seed, trial index, and stream name through SHA-256. Results therefore do not change when worker count or scheduling changes.

```python
study = MonteCarloStudy(
    "detection_study",
    num_trials=1000,
    master_seed=42,
    streams=("scene", "clutter", "noise"),
    max_workers=4,
)
result = study.run(evaluator)
result.write_bundle("results/detection_study", configuration=config)
```

An evaluator receives a `TrialContext`:

```python
def evaluator(context):
    scene_rng = context.rng("scene")
    noise_rng = context.rng("noise")
    return {"rmse_m": float(...) , "detected": bool(...)}
```

Use identical stream draws for all algorithms inside one evaluator when a paired comparison is intended. `result.paired_difference("method_a.rmse", "method_b.rmse")` then reports a confidence interval for matched trial differences.

Each result bundle contains raw trial metrics, summary statistics, a booktabs-compatible LaTeX table fragment, a seed manifest, resolved configuration, and software/environment metadata.
