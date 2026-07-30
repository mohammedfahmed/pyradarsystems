# PyRadarSystems v0.2.0 release validation

Validated on 2026-07-31.

## Source validation

```bash
PYTHONPATH=src pytest -q
```

Result: 18 tests passed.

## Example validation

```bash
PYTHONPATH=src python examples/basic_point_target.py
PYTHONPATH=src python examples/aperture_taper_comparison.py
PYTHONPATH=src python examples/reproducible_taper_study.py \
  --trials 200 --workers 2 \
  --output results/reproducible_taper_study
```

The full taper study produced 200 raw trial rows, 200 seed-manifest rows, confidence-interval summaries, a generated LaTeX table, resolved configuration, environment manifest, and PDF/PNG figures.

The basic point-target example recovered:

- Range: 25.031499 m for a 25 m target
- Radial velocity: -3.041725 m/s for a -3 m/s target
- Azimuth: 12.0 degrees for a 12-degree target

## Wheel validation

```bash
python -m pip wheel . --no-deps --no-build-isolation -w dist
python -m pip install --no-deps --target /tmp/pyradarsystems-wheel \
  dist/pyradarsystems-0.2.0-py3-none-any.whl
PYTHONPATH=/tmp/pyradarsystems-wheel python -m pyradarsystems demo
```

The wheel imported as version 0.2.0 and the installed CLI reproduced the reference point-target result.

## Limitations

This validation does not claim independent MATLAB equivalence, measured-hardware agreement, terrain electromagnetic clutter, or ray-tracing accuracy. Those remain roadmap items.
