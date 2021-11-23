.DEFAULT_GOAL := help

####################
# CONSTANTS
####################
RUN = docker-compose run --rm $(IMAGE_NAME)
RUN_NO_DEPS = docker-compose run --no-deps --rm $(IMAGE_NAME)

REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)

IMAGE_NAME := fidesctl
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LATEST := $(REGISTRY)/$(IMAGE_NAME):latest

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

.PHONY: init-db
init-db: compose-build
	@echo "Checking for new migrations to run..."
	@docker-compose up -d $(IMAGE_NAME)
	@$(RUN) fidesctl init-db
	@make teardown

.PHONY: reset-db
reset-db: compose-build
	@echo "Reset the database..."
	@docker-compose up -d $(IMAGE_NAME)
	@$(RUN) fidesctl reset-db -y
	@make teardown

.PHONY: api
api: compose-build
	@echo "Spinning up the webserver..."
	@docker-compose up $(IMAGE_NAME)
	@make teardown

.PHONY: cli
cli: compose-build
	@echo "Setting up a local development shell... (press CTRL-D to exit)"
	@docker-compose up -d $(IMAGE_NAME)
	@$(RUN) /bin/bash
	@make teardown

####################
# Docker
####################

build:
	docker build --tag $(IMAGE) fidesctl/

push: build
	docker tag $(IMAGE) $(IMAGE_LATEST)
	docker push $(IMAGE)
	docker push $(IMAGE_LATEST)

####################
# CI
####################

black: compose-build
	@$(RUN_NO_DEPS) black --check src/

check-all: check-install fidesctl black pylint mypy xenon pytest
	@echo "Running formatter, linter, typechecker and tests..."

check-install:
	@echo "Checking that fidesctl is installed..."
	@$(RUN_NO_DEPS) fidesctl

fidesctl: compose-build
	@$(RUN_NO_DEPS) fidesctl --local evaluate fides_resources/

mypy: compose-build
	@$(RUN_NO_DEPS) mypy

pylint: compose-build
	@$(RUN_NO_DEPS) pylint src/

pytest: compose-build
	@docker-compose up -d $(IMAGE_NAME)
	@$(RUN) pytest -x

xenon: compose-build
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
	@docker-compose down
	@echo "Teardown complete"

.PHONY: compose-build
compose-build:
	@echo "Build the images required in the docker-compose file..."
	@docker-compose down
	@docker-compose build

.PHONY: docs-serve
docs-serve:
	@docker-compose build docs
	@docker-compose run --rm --service-ports docs \
	/bin/bash -c "pip install -e /fidesctl && mkdocs serve --dev-addr=0.0.0.0:8000"
