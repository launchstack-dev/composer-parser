.PHONY: help install install-dev test test-cov lint format clean build docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  docs         - Build documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy pre-commit

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=composer_parser --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 composer_parser/ tests/
	mypy composer_parser/

format:
	black composer_parser/ tests/
	isort composer_parser/ tests/

# Setup pre-commit hooks
setup-hooks:
	pre-commit install

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Building
build: clean
	python -m build

# Documentation
docs:
	@echo "Documentation is in README.md"
	@echo "Run 'make help' to see available commands"

# Development workflow
dev-setup: install-dev setup-hooks
	@echo "Development environment setup complete!"

# Quick check (lint + test)
check: lint test
	@echo "All checks passed!"

# Release preparation
release-prep: clean format lint test build
	@echo "Release preparation complete!"

# Install package in development mode
install-dev-package:
	pip install -e .

# Uninstall package
uninstall:
	pip uninstall composer-parser -y

# Show package info
package-info:
	python -c "import composer_parser; print(f'Version: {composer_parser.__version__}')"

# Run security checks
security:
	safety check
	bandit -r . -f json -o bandit-report.json

# Performance testing
perf-test:
	python -m pytest tests/ -m "not slow" --durations=10

# Full CI simulation
ci-simulate: clean install-dev format lint test test-cov security
	@echo "CI simulation complete!"

# Help for specific commands
help-install:
	@echo "Installation commands:"
	@echo "  make install           - Install production dependencies"
	@echo "  make install-dev       - Install development dependencies"
	@echo "  make install-dev-package - Install package in development mode"

help-test:
	@echo "Testing commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-cov          - Run tests with coverage"
	@echo "  make perf-test         - Run performance tests"

help-quality:
	@echo "Code quality commands:"
	@echo "  make lint              - Run linting checks"
	@echo "  make format            - Format code"
	@echo "  make security          - Run security checks"
	@echo "  make check             - Run lint + test"

help-dev:
	@echo "Development commands:"
	@echo "  make dev-setup         - Setup development environment"
	@echo "  make ci-simulate       - Simulate CI pipeline"
	@echo "  make release-prep      - Prepare for release" 