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
	@echo clean - Runs various Docker commands to clean up the docker environment including containers, images, volumes, etc.
	@echo ----
	@echo cli - Spins up the database, the api, and starts a shell within a docker container with the local fidesctl files mounted.
	@echo ----
	@echo build - Builds the fidesctl Docker image.
	@echo ----
	@echo check-all - Run all of the available CI checks for fidesctl locally.
	@echo ----
	@echo init-db - Initializes the database docker container and runs migrations. Run this if your database seems to be the cause of test failures.
	@echo ----
	@echo api - Spins up the database and fidesapi, reachable from the host machine at localhost.
	@echo ----
	@echo cli - Spins up the database, fidesapi, and starts a shell within the fidesapi container to run fidesctl commands
	@echo --------------------

####################
# Dev
####################

.PHONY: check-db
check-db: compose-build
	@echo "Check for new migrations to run..."
	@docker-compose down
	@docker-compose run $(IMAGE_NAME) alembic upgrade head
	@make teardown

.PHONY: init-db
init-db: compose-build
	@echo "Drop the db and run the migrations..."
	@docker-compose down
	@docker volume prune -f
	@docker-compose run $(IMAGE_NAME) alembic upgrade head
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
	@docker-compose run $(IMAGE_NAME) /bin/bash
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
	@docker-compose run --no-deps $(IMAGE_NAME) \
	fidesctl

black: compose-build
	@docker-compose run --no-deps $(IMAGE_NAME) \
	black --check src/

mypy: compose-build
	@docker-compose run --no-deps $(IMAGE_NAME) \
	mypy

pylint: compose-build
	@docker-compose run --no-deps $(IMAGE_NAME) \
	pylint src/

pytest: compose-build init-db
	@docker-compose up -d
	@docker-compose run $(IMAGE_NAME) \
	pytest

xenon: compose-build
	@docker-compose run --no-deps $(IMAGE_NAME) \
	xenon src \
	--max-absolute B \
	--max-modules A \
	--max-average A \
	--ignore "data, tests, docs" \
	--exclude "src/fidesctl/_version.py"

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
	@docker-compose up docs
