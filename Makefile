.DEFAULT_GOAL := help

####################
# CONSTANTS
####################

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
	@docker-compose run --rm $(IMAGE_NAME) fidesctl init-db
	@make teardown

.PHONY: reset-db
reset-db: compose-build
	@echo "Reset the database..."
	@docker-compose up -d $(IMAGE_NAME)
	@docker-compose run --rm $(IMAGE_NAME)  fidesctl reset-db -y
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
	@docker-compose run --rm $(IMAGE_NAME) /bin/bash
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

check-all: check-install black pylint mypy xenon pytest
	@echo "Running formatter, linter, typechecker and tests..."

check-install:
	@echo "Checking that fidesctl is installed..."
	@docker-compose run --rm $(IMAGE_NAME) \
	fidesctl

black: compose-build
	@docker-compose run --rm $(IMAGE_NAME) \
	black --check src/

mypy: compose-build
	@docker-compose run --rm $(IMAGE_NAME) \
	mypy

pylint: compose-build
	@docker-compose run --rm $(IMAGE_NAME) \
	pylint src/

pytest: compose-build
	@docker-compose up -d $(IMAGE_NAME)
	@docker-compose run --rm $(IMAGE_NAME) \
	pytest

xenon: compose-build
	@docker-compose run --rm $(IMAGE_NAME) \
	xenon src \
	--max-absolute B \
	--max-modules A \
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

.PHONY: docs-build
docs-build: compose-build
	@docker-compose run --rm --no-deps $(IMAGE_NAME) \
	python generate_openapi.py ../docs/fides/docs/api/openapi.json

.PHONY: docs-serve
docs-serve: docs-build
	@docker-compose build docs
	@docker-compose up docs
