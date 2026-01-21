# Static Analyzer Makefile
# Development automation for production-quality static analysis framework

.PHONY: help install install-dev test test-cov lint format type-check clean build run-sample demo ci-setup

# Default target
help:
	@echo "Static Code Analysis Framework - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Installation:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  test         Run unit tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  lint         Run linting (flake8)"
	@echo "  format       Format code (black)"
	@echo "  type-check   Run type checking (mypy)"
	@echo ""
	@echo "Analysis:"
	@echo "  run-sample   Analyze sample code"
	@echo "  demo         Run full demonstration"
	@echo ""
	@echo "Utilities:"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build distribution packages"
	@echo "  ci-setup     Setup CI environment"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Testing targets
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=static_analyzer --cov-report=html --cov-report=term-missing --cov-report=xml

# Code quality targets
lint:
	flake8 static_analyzer/ tests/ --max-line-length=88 --extend-ignore=E203,W503

format:
	black static_analyzer/ tests/ --line-length=88

type-check:
	mypy static_analyzer/ --ignore-missing-imports

# Analysis targets
run-sample:
	@echo "Analyzing sample code..."
	python -m static_analyzer.cli analyze \
		--path samples/test_violations.c \
		--config samples/static_analyzer_config.yaml \
		--output analysis_results.json \
		--format json \
		--verbose

demo: install
	@echo "=== Static Analysis Framework Demonstration ==="
	@echo ""
	
	@echo "1. Creating default configuration..."
	python -m static_analyzer.cli init-config --output demo_config.yaml
	@echo ""
	
	@echo "2. Listing available rules..."
	python -m static_analyzer.cli list-rules
	@echo ""
	
	@echo "3. Validating configuration..."
	python -m static_analyzer.cli validate-config --config demo_config.yaml
	@echo ""
	
	@echo "4. Analyzing sample code with violations..."
	python -m static_analyzer.cli analyze \
		--path samples/test_violations.c \
		--config demo_config.yaml \
		--output demo_violations.json \
		--format json \
		--verbose
	@echo ""
	
	@echo "5. Analyzing compliant code..."
	python -m static_analyzer.cli analyze \
		--path samples/compliant_code.c \
		--config demo_config.yaml \
		--output demo_compliant.json \
		--format json \
		--verbose
	@echo ""
	
	@echo "6. Results summary:"
	@echo "   - Violations found: $$(jq '.summary.total_violations' demo_violations.json 2>/dev/null || echo 'N/A')"
	@echo "   - Compliant analysis: $$(jq '.summary.total_violations' demo_compliant.json 2>/dev/null || echo 'N/A')"
	@echo ""
	@echo "Demo complete! Check demo_*.json files for detailed results."

# Development workflow - run all quality checks
check-all: format lint type-check test

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Build distribution packages
build: clean
	python -m build

# CI setup
ci-setup:
	@echo "Setting up CI environment..."
	sudo apt-get update
	sudo apt-get install -y clang libclang-dev
	pip install --upgrade pip
	pip install -r requirements.txt

# Development server (if implementing web interface later)
serve:
	@echo "Static analysis server not implemented yet"
	@echo "Use CLI interface: python -m static_analyzer.cli --help"

# Documentation generation (if adding docs)
docs:
	@echo "Documentation generation not implemented yet"
	@echo "See README.md for usage instructions"

# Performance testing
perf-test:
	@echo "Running performance test on sample files..."
	time python -m static_analyzer.cli analyze \
		--path samples/ \
		--recursive \
		--output perf_test.json \
		--verbose

# Security check (using bandit if available)
security:
	@echo "Running security checks..."
	@command -v bandit >/dev/null 2>&1 && bandit -r static_analyzer/ || echo "bandit not installed"

# Generate requirements.txt from pyproject.toml
requirements:
	pip-compile pyproject.toml --output-file requirements.txt

# Quick development cycle
dev: format lint type-check test run-sample
	@echo "Development cycle complete!"

# Production deployment check
prod-check: check-all perf-test
	@echo "Production readiness check complete!"
	@echo "Ready for deployment if all checks passed."
