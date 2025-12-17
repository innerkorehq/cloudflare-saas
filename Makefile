.PHONY: install test lint format clean build deploy docs help

help:
	@echo "Cloudflare SaaS Platform - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install        Install package and dependencies"
	@echo "  make install-dev    Install with development dependencies"
	@echo "  make install-docs   Install documentation dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run tests"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make test-watch     Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linters (ruff, mypy)"
	@echo "  make format         Format code (black, ruff)"
	@echo "  make check          Run all checks (lint + test)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs           Build documentation"
	@echo "  make docs-serve     Build and serve documentation"
	@echo "  make docs-clean     Clean documentation build"
	@echo ""
	@echo "Deployment:"
	@echo "  make build          Build distribution packages"
	@echo "  make deploy         Deploy to PyPI"
	@echo "  make deploy-infra   Deploy infrastructure"
	@echo "  make destroy-infra  Destroy infrastructure"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo "  make docker-stop    Stop Docker container"
	@echo ""
	@echo "API:"
	@echo "  make run-api        Run FastAPI development server"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          Clean build artifacts"
	@echo "  make clean-all      Clean all generated files"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,web]"

install-docs:
	pip install -r docs/requirements.txt

test:
	pytest tests/ -v --log-cli-level=INFO

test-cov:
	pytest tests/ --cov=cloudflare_saas --cov-report=html --cov-report=term --cov-report=xml

test-watch:
	pytest-watch tests/ -v

lint:
	@echo "Running ruff..."
	ruff check cloudflare_saas/ examples/ tests/
	@echo "Running mypy..."
	mypy cloudflare_saas/

format:
	@echo "Formatting with black..."
	black cloudflare_saas/ examples/ tests/
	@echo "Auto-fixing with ruff..."
	ruff check --fix cloudflare_saas/ examples/ tests/

check: lint test
	@echo "All checks passed!"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .coverage htmlcov/ coverage.xml
	rm -rf terraform_generated/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

clean-all: clean docs-clean
	@echo "Cleaning all generated files..."
	rm -rf .mypy_cache .ruff_cache
	rm -rf *.log

build:
	@echo "Building distribution packages..."
	python -m build

# Documentation targets
docs:
	@echo "Building documentation..."
	cd docs && $(MAKE) html
	@echo "Documentation built in docs/build/html/"

docs-serve: docs
	@echo "Serving documentation at http://localhost:8001"
	cd docs/build/html && python -m http.server 8001

docs-clean:
	@echo "Cleaning documentation build..."
	cd docs && $(MAKE) clean

# Infrastructure deployment
deploy-infra:
	python examples/deploy_infrastructure.py

destroy-infra:
	python examples/deploy_infrastructure.py destroy

# API server
run-api:
	@echo "Starting FastAPI development server..."
	uvicorn examples.fastapi_integration:app --reload --host 0.0.0.0 --port 8000

# Docker targets
docker-build:
	@echo "Building Docker image..."
	docker build -t cloudflare-saas-api .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 --env-file .env cloudflare-saas-api

docker-stop:
	@echo "Stopping Docker containers..."
	docker stop $$(docker ps -q --filter ancestor=cloudflare-saas-api) 2>/dev/null || true

# PyPI deployment
deploy: clean build
	@echo "Deploying to PyPI..."
	twine upload dist/*

deploy-test: clean build
	@echo "Deploying to Test PyPI..."
	twine upload --repository testpypi dist/*