"""Aperture-taper construction and explicit normalization policies."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from scipy.signal.windows import chebwin, taylor

TaperKind = Literal["uniform", "hann", "hamming", "blackman", "taylor", "chebyshev"]
NormalizationPolicy = Literal[
    "none",
    "constant_total_power",
    "constant_peak_power",
    "constant_broadside_gain",
]


@dataclass(frozen=True)
class TaperNormalizationReport:
    policy: str
    scale: float
    input_total_power: float
    output_total_power: float
    output_peak_power: float
    output_broadside_gain: float

    def as_dict(self) -> dict[str, float | str]:
        return asdict(self)


def make_taper(
    num_elements: int,
    kind: TaperKind = "uniform",
    *,
    sidelobe_level_db: float = 30.0,
    nbar: int = 4,
) -> np.ndarray:
    """Construct a real symmetric taper without applying normalization."""

    if num_elements <= 0:
        raise ValueError("num_elements must be positive")
    if sidelobe_level_db <= 0:
        raise ValueError("sidelobe_level_db must be positive")
    if nbar < 2:
        raise ValueError("nbar must be at least 2")
    kind = str(kind).lower()
    if kind == "uniform":
        weights = np.ones(num_elements)
    elif kind == "hann":
        weights = np.hanning(num_elements)
    elif kind == "hamming":
        weights = np.hamming(num_elements)
    elif kind == "blackman":
        weights = np.blackman(num_elements)
    elif kind == "taylor":
        weights = taylor(num_elements, nbar=nbar, sll=sidelobe_level_db, norm=True)
    elif kind == "chebyshev":
        weights = chebwin(num_elements, at=sidelobe_level_db, sym=True)
    else:
        raise ValueError(f"unsupported taper kind: {kind}")
    return np.asarray(weights, dtype=complex)


def normalize_taper(
    weights: np.ndarray,
    policy: NormalizationPolicy = "constant_total_power",
    *,
    reference_weights: np.ndarray | None = None,
) -> tuple[np.ndarray, TaperNormalizationReport]:
    """Normalize an aperture taper against a reference aperture.

    The default reference is an all-ones aperture of equal length, which keeps
    the existing uniform-array convention unchanged:

    - ``constant_total_power``: ``sum(|w|^2) = N``
    - ``constant_peak_power``: ``max(|w|^2) = 1``
    - ``constant_broadside_gain``: ``|sum(w)| = N``
    """

    values = np.asarray(weights, dtype=complex)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("weights must be a non-empty 1D array")
    reference = (
        np.ones(values.size, dtype=complex)
        if reference_weights is None
        else np.asarray(reference_weights, dtype=complex)
    )
    if reference.shape != values.shape:
        raise ValueError("reference_weights must match weights shape")
    input_power = float(np.sum(np.abs(values) ** 2))
    if input_power <= 0:
        raise ValueError("weights must contain non-zero energy")

    if policy == "none":
        scale = 1.0
    elif policy == "constant_total_power":
        target = float(np.sum(np.abs(reference) ** 2))
        scale = np.sqrt(target / input_power)
    elif policy == "constant_peak_power":
        source = float(np.max(np.abs(values)))
        target = float(np.max(np.abs(reference)))
        if source <= 0:
            raise ValueError("weights must contain a non-zero coefficient")
        scale = target / source
    elif policy == "constant_broadside_gain":
        source = float(np.abs(np.sum(values)))
        target = float(np.abs(np.sum(reference)))
        if source <= np.finfo(float).eps:
            raise ValueError("weights have zero broadside coherent sum")
        scale = target / source
    else:
        raise ValueError(f"unsupported normalization policy: {policy}")

    normalized = values * scale
    report = TaperNormalizationReport(
        policy=policy,
        scale=float(scale),
        input_total_power=input_power,
        output_total_power=float(np.sum(np.abs(normalized) ** 2)),
        output_peak_power=float(np.max(np.abs(normalized) ** 2)),
        output_broadside_gain=float(np.abs(np.sum(normalized)) ** 2),
    )
    return normalized, report
