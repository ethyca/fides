.DEFAULT_GOAL := help

####################
# CONSTANTS
####################

REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)

IMAGE_NAME := fidesops
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LATEST := $(REGISTRY)/$(IMAGE_NAME):latest


####################
# Defaults
####################

.PHONY: help
help:
	@echo "Under Construction, please read the Makefile directly!"

####################
# Dev
####################

init-db: compose-build
	@echo "Check for new migrations to run..."
	@docker-compose run --rm $(IMAGE_NAME) \
	python -c "\
	from fidesops.db.database import init_db; \
	from fidesops.core.config import config; \
	init_db(config.database.SQLALCHEMY_DATABASE_URI);"

reset-db:
	@echo "Resetting and re-initializing the application db..."
	@make teardown
	@docker volume rm fidesops_app-db-data || echo "No app DB found, continuing!"
	@make init-db

server: compose-build
	@docker-compose up

server-shell: compose-build
	@docker-compose run $(IMAGE_NAME) /bin/bash

integration-shell: compose-build
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml run $(IMAGE_NAME) /bin/bash

integration-env: compose-build
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml up

quickstart: compose-build
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml up -d
	@docker exec -it fidesops python quickstart.py

####################
# Docker
####################

docker-build:
	docker build --tag $(IMAGE) .

docker-push:
	docker tag $(IMAGE) $(IMAGE_LATEST)
	docker push $(IMAGE)
	docker push $(IMAGE_LATEST)

####################
# CI
####################

check-all: black-ci pylint mypy pytest pytest-integration check-migrations

black-ci: compose-build
	@echo "Running black checks..."
	@docker-compose run $(IMAGE_NAME) \
		black --check src/ \
		|| (echo "Error running 'black --check', please run 'make black' to format your code!"; exit 1)

check-migrations: compose-build
	@echo "Check if there are unrun migrations..."
	@docker-compose run --rm $(IMAGE_NAME) \
	python -c "\
	from fidesops.db.database import check_missing_migrations; \
	from fidesops.core.config import config; \
	check_missing_migrations(config.database.SQLALCHEMY_DATABASE_URI);"

pylint: compose-build
	@echo "Running pylint checks..."
	@docker-compose run $(IMAGE_NAME) \
		pylint src/

mypy: compose-build
	@echo "Running mypy checks..."
	@docker-compose run $(IMAGE_NAME) \
		mypy --ignore-missing-imports src/

pytest: compose-build
	@echo "Running pytest unit tests..."
	@docker-compose run $(IMAGE_NAME) \
		pytest $(pytestpath) -m "not integration and not integration_erasure and not external_integration"

# Run the pytest integration tests.
pytest-integration-access: compose-build
	@echo "Building additional Docker images for integration tests..."
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml build
	@echo "Bringing up the integration environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml up -d
	@echo "Waiting 10s for integration containers to be ready..."
	@sleep 10
	@echo "Running pytest integration tests..."
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml \
		run $(IMAGE_NAME) \
		pytest $(pytestpath) -m integration
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml down --remove-orphans

pytest-integration-erasure: compose-build
	@echo "Building additional Docker images for integration tests..."
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml build
	@echo "Running pytest integration tests..."
	@docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml \
		run $(IMAGE_NAME) \
		pytest $(pytestpath) -m "integration_erasure"

# These tests connect to external third-party test databases
pytest-external-integration: compose-build
	@echo "Running tests that connect to external third party test databases"
	@docker-compose run -e REDSHIFT_TEST_URI -e SNOWFLAKE_TEST_URI $(IMAGE_NAME) \
		pytest $(pytestpath) -m "external_integration"


####################
# Utils
####################

.PHONY: black
black: compose-build
	@echo "Running black formatting against the src/ directory..."
	@docker-compose run $(IMAGE_NAME) \
	black src/

.PHONY: clean
clean:
	@echo "Cleaning project temporary files and installed dependencies..."
	@docker system prune -a --volumes
	@echo "Clean complete!"

.PHONY: compose-build
compose-build:
	@echo "Tearing down the docker compose images, network, etc..."
	@docker-compose down --remove-orphans
	@docker-compose build

.PHONY: teardown
teardown:
	@echo "Tearing down the dev environment..."
	@docker-compose down --remove-orphans
	@echo "Teardown complete"

.PHONY: docs-build
docs-build: compose-build
	@docker-compose run --rm $(IMAGE_NAME) \
	python generate_openapi.py ./docs/fidesops/docs/api/openapi.json

.PHONY: docs-serve
docs-serve: docs-build
	@docker-compose build docs
	@docker-compose up docs
