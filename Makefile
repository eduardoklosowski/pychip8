# Project

srcdir = src
testsdir = tests


# Build

.PHONY: build

build:
	poetry build


# Init

.PHONY: init

init:
	poetry install --sync


# Format

.PHONY: fmt

fmt:
	poetry run ruff check --select I001 --fix $(srcdir) $(testsdir)
	poetry run ruff format $(srcdir) $(testsdir)


# Lint

.PHONY: lint lint-poetry lint-ruff-format lint-ruff-check lint-mypy

lint: lint-poetry lint-ruff-format lint-ruff-check lint-mypy

lint-poetry:
	poetry check --lock

lint-ruff-format:
	poetry run ruff format --diff $(srcdir) $(testsdir)

lint-ruff-check:
	poetry run ruff check $(srcdir) $(testsdir)

lint-mypy:
	poetry run mypy --show-error-context --pretty $(srcdir) $(testsdir)


# Tests

.PHONY: test test-pytest

test: test-pytest

test-pytest:
	poetry run pytest --cov=pychip8 --cov-report=term-missing --no-cov-on-fail $(testsdir)


# Clean

.PHONY: clean clean-build clean-pycache clean-python-tools dist-clean

clean: clean-build clean-pycache clean-python-tools

clean-build:
	rm -rf dist

clean-pycache:
	find $(srcdir) $(testsdir) -name '__pycache__' -exec rm -rf {} +
	find $(srcdir) $(testsdir) -type d -empty -delete

clean-python-tools:
	rm -rf dist .ruff_cache .mypy_cache .pytest_cache .coverage .coverage.*

dist-clean: clean
	rm -rf .venv
