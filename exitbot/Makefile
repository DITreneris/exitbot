.PHONY: help setup dev test lint build deploy logs clean

# Variables
DOCKER_COMPOSE=docker-compose
PYTHON=python
PIP=pip
PYTEST=pytest
FLAKE8=flake8

help:
	@echo "ExitBot Makefile Commands:"
	@echo "  setup      - Set up development environment"
	@echo "  dev        - Run development server"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  build      - Build Docker image"
	@echo "  deploy     - Deploy with Docker Compose"
	@echo "  logs       - View Docker logs"
	@echo "  clean      - Clean up temporary files"

setup:
	cp -n .env.template .env || true
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

dev:
	ENVIRONMENT=development $(PYTHON) -m app.main

test:
	$(PYTEST)

lint:
	$(FLAKE8) exitbot

build:
	$(DOCKER_COMPOSE) build

deploy:
	$(DOCKER_COMPOSE) up -d

logs:
	$(DOCKER_COMPOSE) logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name ".eggs" -exec rm -rf {} + 