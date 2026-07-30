.PHONY: install test demo clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest

demo:
	python examples/basic_point_target.py

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info results
