PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: install lint typecheck test run-api run-scheduler run-worker docker-build docker-up docker-down terraform-format terraform-validate

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -r requirements-dev.txt

lint:
	$(BIN)/ruff format --check .
	$(BIN)/ruff check .

typecheck:
	$(BIN)/python -m mypy app tests

test:
	$(BIN)/python -m pytest

run-api:
	$(BIN)/uvicorn app.api.main:app --reload

run-scheduler:
	$(BIN)/python -m app.scheduler.main

run-worker:
	$(BIN)/python -m app.worker.main

docker-build:
	docker build -t aws-ecs-internal-service-monitor:local .

docker-up:
	docker compose up --build api

docker-down:
	docker compose down

terraform-format:
	terraform -chdir=terraform/environments/dev fmt -recursive

terraform-validate:
	terraform -chdir=terraform/environments/dev init -backend=false
	terraform -chdir=terraform/environments/dev validate
