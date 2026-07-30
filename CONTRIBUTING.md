# Contributing

Contributions that improve correctness, validation, documentation, or radar-model coverage are welcome.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell
python -m pip install -e ".[dev]"
python -m pytest
```

## Contribution requirements

1. Open an issue before a large architectural change.
2. Add tests for new physical models and processing algorithms.
3. State coordinate, sign, normalization, and unit conventions explicitly.
4. Include an analytical, numerical, statistical, or measured-data validation case.
5. Keep generated outputs, raw captures, and build products outside version control.
6. Update the changelog and relevant documentation.

## Pull requests

A pull request should explain the radar problem, implementation approach, assumptions, validation evidence, and any known limitations. All tests must pass.
