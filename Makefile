.DEFAULT_GOAL := help

####################
# CONSTANTS
####################
REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)

# Various Image Names
IMAGE_NAME := fidesctl
LOCAL_IMAGE_NAME := ethyca/fidesctl:local
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LATEST := $(REGISTRY)/$(IMAGE_NAME):latest

# Run in Compose
RUN = docker-compose run --rm $(IMAGE_NAME)
RUN_NO_DEPS = docker-compose run --no-deps --rm $(IMAGE_NAME)

# Run using standalone containers
RUN_LOCAL = docker run --rm $(LOCAL_IMAGE_NAME)

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

.PHONY: black
black:
	@$(RUN_LOCAL) black --check src/

.PHONY: check-all
check-all: compose-build check-install fidesctl black pylint mypy xenon pytest
	@echo "Running formatter, linter, typechecker and tests..."

.PHONY: check-install
check-install:
	@echo "Checking that fidesctl is installed..."
	@$(RUN_LOCAL) fidesctl

.PHONY: fidesctl
fidesctl:
	@$(RUN_LOCAL) fidesctl --local evaluate fides_resources/

.PHONY: mypy
mypy:
	@$(RUN_LOCAL) mypy

.PHONY: pylint
pylint:
	@$(RUN_LOCAL) pylint src/

.PHONY: pytest
pytest: compose-build
	@$(RUN) pytest -x

.PHONY: xenon
xenon:
	@$(RUN_LOCAL) xenon src \
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
	@docker-compose build fidesctl

.PHONY: docs-build
docs-build: compose-build
	@docker-compose run --rm $(IMAGE_NAME) \
	python generate_openapi.py ../docs/fides/docs/api/openapi.json

.PHONY: docs-serve
docs-serve: docs-build
	@docker-compose build docs
	@docker-compose run --rm --service-ports docs \
	/bin/bash -c "pip install -e /fidesctl && mkdocs serve --dev-addr=0.0.0.0:8000"
