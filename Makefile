# Project

SRC_DIR := src
TESTS_DIR := tests
VENV_DIR := .venv


# Build

.PHONY: build

build:
	poetry build


# Init

.PHONY: init

init:
	poetry sync


# Format

.PHONY: fmt

fmt:
	poetry run ruff check --select I001 --fix $(SRC_DIR) $(TESTS_DIR)
	poetry run ruff format $(SRC_DIR) $(TESTS_DIR)


# Lint

.PHONY: lint lint-poetry lint-ruff-format lint-ruff-check lint-mypy

lint: lint-poetry lint-ruff-format lint-ruff-check lint-mypy

lint-poetry:
	poetry check --lock

lint-ruff-format:
	poetry run ruff format --diff $(SRC_DIR) $(TESTS_DIR)

lint-ruff-check:
	poetry run ruff check $(SRC_DIR) $(TESTS_DIR)

lint-mypy:
	poetry run mypy --show-error-context --pretty $(SRC_DIR) $(TESTS_DIR)


# Tests

.PHONY: test test-pytest test-coverage-report

test: test-pytest

test-pytest .coverage:
	poetry run pytest --cov=pychip8 --cov-report=term-missing --no-cov-on-fail $(TESTS_DIR)

test-coverage-report: .coverage
	poetry run coverage html


# Clean

.PHONY: clean clean-build clean-pycache clean-python-tools dist-clean

clean: clean-build clean-pycache clean-python-tools

clean-build:
	rm -rf build dist $(SRC_DIR)/*.egg-info

clean-pycache:
	find $(SRC_DIR) $(TESTS_DIR) -name '__pycache__' -exec rm -rf {} +
	find $(SRC_DIR) $(TESTS_DIR) -type d -empty -delete

clean-python-tools:
	rm -rf .ruff_cache .mypy_cache .pytest_cache .coverage .coverage.* htmlcov

dist-clean: clean
	rm -rf $(VENV_DIR)
