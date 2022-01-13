.DEFAULT_GOAL := help

####################
# CONSTANTS
####################
REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)

# Image Names & Tags
IMAGE_NAME := fidesctl
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LOCAL := $(REGISTRY)/$(IMAGE_NAME):local
IMAGE_LATEST := $(REGISTRY)/$(IMAGE_NAME):latest

# Run in Compose
RUN = docker compose run --rm $(IMAGE_NAME)
RUN_NO_DEPS = docker compose run --no-deps --rm $(IMAGE_NAME)

.PHONY: help
help:
	@echo --------------------
	@echo Development Targets:
	@echo ----
	@echo clean - Runs various Docker commands to clean up the docker environment including containers, images, volumes, etc. This will wipe out everything!
	@echo ----
	@echo cli - Spins up the database, the api, and starts a shell within a Docker container with the local Fidesctl files mounted.
	@echo ----
	@echo build - Builds the Fidesctl Docker image.
	@echo ----
	@echo check-all - Run all of the available CI checks for Fidesctl locally.
	@echo ----
	@echo init-db - Run any available migrations.
	@echo ----
	@echo api - Spins up the database and API, reachable from the host machine at localhost.
	@echo ----
	@echo cli - Spins up the database, API, and starts a shell within the API container to run Fidesctl CLI commands.
	@echo --------------------

####################
# Dev
####################

.PHONY: reset-db
reset-db: build-local
	@echo "Reset the database..."
	@docker compose up -d $(IMAGE_NAME)
	@$(RUN) fidesctl reset-db -y
	@make teardown

.PHONY: api
api: build-local
	@echo "Spinning up the webserver..."
	@docker compose up $(IMAGE_NAME)
	@make teardown

.PHONY: cli
cli: build-local
	@echo "Setting up a local development shell... (press CTRL-D to exit)"
	@docker compose up -d $(IMAGE_NAME)
	@$(RUN) /bin/bash
	@make teardown

.PHONY: cli-integration
cli-integration: build-local
	@echo "Setting up a local development shell... (press CTRL-D to exit)"
	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml up -d $(IMAGE_NAME)
	@$(RUN) /bin/bash
	@make teardown
####################
# Docker
####################

build:
	docker build --tag $(IMAGE) fidesctl/

build-local:
	docker build --tag $(IMAGE_LOCAL) fidesctl/

push: build
	docker tag $(IMAGE) $(IMAGE_LATEST)
	docker push $(IMAGE)
	docker push $(IMAGE_LATEST)

####################
# CI
####################

black:
	@$(RUN_NO_DEPS) black --check src/

# The order of dependent targets here is intentional
check-all: build-local check-install fidesctl black pylint mypy xenon pytest-unit pytest-integration pytest-external
	@echo "Running formatter, linter, typechecker and tests..."

check-install:
	@echo "Checking that fidesctl is installed..."
	@$(RUN_NO_DEPS) fidesctl

.PHONY: fidesctl
fidesctl:
	@$(RUN_NO_DEPS) fidesctl --local evaluate fides_resources/

mypy:
	@$(RUN_NO_DEPS) mypy

pylint:
	@$(RUN_NO_DEPS) pylint src/

pytest-unit:
	@docker compose up -d $(IMAGE_NAME)
	@$(RUN_NO_DEPS) \
	pytest -x -m unit

pytest-integration:
	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml up -d $(IMAGE_NAME)
	@docker compose run --rm $(IMAGE_NAME) \
	pytest -x -m integration
	@make teardown

pytest-external:
	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml up -d $(IMAGE_NAME)
	@docker compose run -e SNOWFLAKE_FIDESCTL_PASSWORD --rm $(IMAGE_NAME) \
	pytest -x -m external
	@make teardown

xenon:
	@$(RUN_NO_DEPS) xenon src \
	--max-absolute B \
	--max-modules B \
	--max-average A \
	--ignore "data, tests, docs" \
	--exclude "src/fidesctl/core/annotate_dataset.py,src/fidesctl/_version.py"

####################
# Utils
####################

.PHONY: clean
clean:
	@echo "Cleaning project temporary files and installed dependencies..."
	@docker system prune -a --volumes
	@echo "Clean complete!"

.PHONY: teardown
teardown:
	@echo "Tearing down the dev environment..."
	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml down --remove-orphans
	@echo "Teardown complete"

.PHONY: docs-build
docs-build: build-local
	@docker compose run --rm $(IMAGE_NAME) \
	python generate_openapi.py ../docs/fides/docs/api/openapi.json

.PHONY: docs-serve
docs-serve: docs-build
	@docker compose build docs
	@docker compose run --rm --service-ports docs \
	/bin/bash -c "pip install -e /fidesctl && mkdocs serve --dev-addr=0.0.0.0:8000"
