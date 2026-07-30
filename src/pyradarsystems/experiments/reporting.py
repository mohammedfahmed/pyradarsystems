"""Small dependency-free helpers for generated LaTeX result tables."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def _format(value: object, float_format: str) -> str:
    if isinstance(value, float):
        return format(value, float_format)
    return latex_escape(value)


def write_latex_table(
    path: str | Path,
    rows: Sequence[Mapping[str, object]],
    columns: Sequence[str],
    *,
    headers: Mapping[str, str] | None = None,
    float_format: str = ".6g",
) -> Path:
    """Write a booktabs-compatible ``tabular`` fragment.

    The function intentionally emits only a table fragment so papers can add
    their own caption, label, sizing, and placement policy.
    """

    if not rows:
        raise ValueError("rows cannot be empty")
    if not columns:
        raise ValueError("columns cannot be empty")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    labels = headers or {}
    alignment = "l" + "r" * (len(columns) - 1)
    lines = [f"\\begin{{tabular}}{{{alignment}}}", r"\toprule"]
    heading = " & ".join(
        latex_escape(labels.get(column, column)) for column in columns
    )
    lines.append(heading + r" \\")
    lines.append(r"\midrule")
    for row in rows:
        lines.append(" & ".join(_format(row[column], float_format) for column in columns) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination
