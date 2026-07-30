"""Statistical summaries for Monte Carlo radar experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.stats import t


@dataclass(frozen=True)
class ConfidenceInterval:
    count: int
    mean: float
    standard_deviation: float
    standard_error: float
    confidence: float
    lower: float
    upper: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def mean_confidence_interval(
    values: np.ndarray | list[float],
    *,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    samples = np.asarray(values, dtype=float)
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError("values must be a non-empty 1D sequence")
    if not np.all(np.isfinite(samples)):
        raise ValueError("values must be finite")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    count = int(samples.size)
    mean = float(np.mean(samples))
    std = float(np.std(samples, ddof=1)) if count > 1 else 0.0
    standard_error = std / np.sqrt(count) if count > 0 else float("nan")
    margin = (
        float(t.ppf((1.0 + confidence) / 2.0, df=count - 1)) * standard_error
        if count > 1
        else 0.0
    )
    return ConfidenceInterval(
        count=count,
        mean=mean,
        standard_deviation=std,
        standard_error=float(standard_error),
        confidence=float(confidence),
        lower=float(mean - margin),
        upper=float(mean + margin),
    )
