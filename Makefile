.PHONY: install test demo taper-study build clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest

demo:
	python examples/basic_point_target.py

taper-study:
	python examples/reproducible_taper_study.py --trials 200 --workers 1

build:
	python -m build

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info results
