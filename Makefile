# Project

srcdir = pychip8
testsdir = tests


# Build

.PHONY: build
build:
	poetry build


# Formatter

.PHONY: fmt fmt-isort
fmt: fmt-isort

fmt-isort:
	poetry run isort --only-modified $(srcdir) $(testsdir)


# Lint

.PHONY: lint lint-poetry lint-isort lint-flake8 lint-mypy lint-bandit
lint: lint-poetry lint-isort lint-flake8 lint-mypy lint-bandit

lint-poetry:
	poetry check

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
	poetry run pytest --numprocesses=auto $(testsdir)


# Clean

.PHONY: clean
clean:
	find $(srcdir) $(testsdir) -name '__pycache__' -exec rm -rf {} +
	find $(srcdir) $(testsdir) -type d -empty -delete
	rm -rf dist .mypy_cache .pytest_cache .coverage
