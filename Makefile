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
	poetry run isort --only-modified $(srcdir) $(testsdir)


# Lint

.PHONY: lint lint-poetry lint-isort lint-flake8 lint-mypy lint-bandit

lint: lint-poetry lint-isort lint-flake8 lint-mypy lint-bandit

lint-poetry:
	poetry check --lock

lint-isort:
	poetry run isort --check --diff $(srcdir) $(testsdir)

lint-flake8:
	poetry run flake8 --show-source $(srcdir) $(testsdir)

lint-mypy:
	poetry run mypy --show-error-context --pretty $(srcdir) $(testsdir)

lint-bandit:
	poetry run bandit --silent --recursive $(srcdir)


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
	rm -rf dist .mypy_cache .pytest_cache .coverage .coverage.*

dist-clean: clean
	rm -rf .venv
