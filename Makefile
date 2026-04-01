.PHONY: help install install-dev test clean lint format

help:
	@echo "ACRCloud CLI - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install the CLI tool"
	@echo "  install-dev  - Install in development mode with test dependencies"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean build artifacts"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code with black"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	python -m unittest discover tests -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 acrcloud_cli tests

format:
	black acrcloud_cli tests
