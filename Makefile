.DEFAULT_GOAL := help

####################
# CONSTANTS
####################
REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)
WITH_TEST_CONFIG := -f tests/test_config.toml

# Image Names & Tags
IMAGE_NAME := fidesctl
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LOCAL := $(REGISTRY)/$(IMAGE_NAME):local
IMAGE_LATEST := $(REGISTRY)/$(IMAGE_NAME):latest

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
ifeq "$(CI)" "true"
    CI_ARGS:=--no-TTY
endif

# If FIDESCTL__CLI__ANALYTICS_ID is set in the local environment, use its value as the analytics_id
ANALYTICS_ID_OVERRIDE = -e FIDESCTL__CLI__ANALYTICS_ID

# Run in Compose
RUN = docker compose run --rm $(ANALYTICS_ID_OVERRIDE) $(CI_ARGS) $(IMAGE_NAME)
RUN_NO_DEPS = docker compose run --no-deps --rm $(ANALYTICS_ID_OVERRIDE) $(CI_ARGS) $(IMAGE_NAME)
START_APP = docker compose up -d $(IMAGE_NAME)

.PHONY: help
help:
	@echo --------------------
	@echo Development Targets:
	@echo ----
	@echo clean - Runs various Docker commands to clean up the docker environment including containers, images, volumes, etc. This will wipe out everything!
	@echo ----
	@echo build - Builds the Fidesctl Docker image.
	@echo ----
	@echo check-all - Run all of the available CI checks for Fidesctl locally.
	@echo ----
	@echo reset-db - Wipes all user-created data and resets the database back to its freshly initialized state.
	@echo ----
	@echo api - Spins up the database and API, reachable from the host machine at localhost.
	@echo ----
	@echo cli - Spins up the database, API, and starts a shell within the API container to run Fidesctl CLI commands.
	@echo ----
	@echo cli-integration - Spins up the cli with additional containers needed for integration testing.
	@echo --------------------

####################
# Dev
####################

.PHONY: reset-db
reset-db: build-local
	@echo "Reset the database..."
	@$(START_APP)
	@$(RUN) fidesctl db reset -y
	@make teardown

.PHONY: api
api: build-local
	@echo "Spinning up the webserver..."
	@docker compose up $(IMAGE_NAME)
	@make teardown

.PHONY: cli
cli: build-local
	@echo "Setting up a local development shell... (press CTRL-D to exit)"
	@$(START_APP)
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
check-all: build-local check-install fidesctl fidesctl-db-scan black \
			pylint mypy xenon pytest-unit pytest-integration pytest-external
	@echo "Running formatter, linter, typechecker and tests..."

check-install:
	@echo "Checking that fidesctl is installed..."
	@$(RUN_NO_DEPS) fidesctl ${WITH_TEST_CONFIG}

.PHONY: fidesctl
fidesctl:
	@$(RUN_NO_DEPS) fidesctl --local ${WITH_TEST_CONFIG} evaluate

fidesctl-db-scan:
	@$(START_APP)
	@$(RUN) fidesctl ${WITH_TEST_CONFIG} scan dataset db \
	"postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test"

mypy:
	@$(RUN_NO_DEPS) mypy

pylint:
	@$(RUN_NO_DEPS) pylint src/

pytest-unit:
	@docker compose up -d $(IMAGE_NAME)
	@$(RUN_NO_DEPS) pytest -x -m unit

pytest-integration:
	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml up -d $(IMAGE_NAME)
	@docker compose run --rm $(CI_ARGS) $(IMAGE_NAME) \
	pytest -x -m integration
	@make teardown

pytest-external:
	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml up -d $(IMAGE_NAME)
	@docker compose run \
	-e SNOWFLAKE_FIDESCTL_PASSWORD \
	-e REDSHIFT_FIDESCTL_PASSWORD \
	-e AWS_ACCESS_KEY_ID \
	-e AWS_SECRET_ACCESS_KEY \
	-e AWS_DEFAULT_REGION \
	-e OKTA_CLIENT_TOKEN \
	--rm $(CI_ARGS) $(IMAGE_NAME) \
	pytest -x -m external
	@make teardown

xenon:
	@$(RUN_NO_DEPS) xenon src \
	--max-absolute B \
	--max-modules B \
	--max-average A \
	--ignore "data, tests, docs" \
	--exclude "src/fidesctl/core/annotate_dataset.py,src/fidesctl/_version.py,src/fidesctl/cli/__init__.py"

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
	@docker compose run --rm $(CI_ARGS) $(IMAGE_NAME) \
	python generate_docs.py ../docs/fides/docs/

.PHONY: docs-serve
docs-serve: docs-build
	@docker compose build docs
	@docker compose run --rm --service-ports $(CI_ARGS) docs \
	/bin/bash -c "pip install -e /fidesctl && mkdocs serve --dev-addr=0.0.0.0:8000"
