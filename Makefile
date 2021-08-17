.DEFAULT_GOAL := help

####################
# CONSTANTS
####################

REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)

# Server
SERVER_IMAGE_NAME := fidesapi
SERVER_IMAGE := $(REGISTRY)/$(SERVER_IMAGE_NAME):$(IMAGE_TAG)
SERVER_IMAGE_LATEST := $(REGISTRY)/$(SERVER_IMAGE_NAME):latest
# CLI
CLI_IMAGE_NAME := fidesctl
CLI_IMAGE := $(REGISTRY)/$(CLI_IMAGE_NAME):$(IMAGE_TAG)
CLI_IMAGE_LATEST := $(REGISTRY)/$(CLI_IMAGE_NAME):latest

.PHONY: help
help:
	@echo --------------------
	@echo Development Targets:
	@echo ----
	@echo clean - Runs various Docker commands to clean up the docker environment including containers, images, volumes, etc.
	@echo ----
	@echo cli - Spins up the database, the api, and starts a shell within a docker container with the local fidesctl files mounted.
	@echo ----
	@echo cli-build - Builds the fidesctl Docker image.
	@echo ----
	@echo fidesctl-check-all - Run all of the available CI checks for fidesctl locally.
	@echo ----
	@echo init-db - Initializes the database docker container and runs migrations. Run this if your database seems to be the cause of test failures.
	@echo ----
	@echo server - Spins up the database and fidesapi, reachable from the host machine at localhost.
	@echo ----
	@echo server-build - Builds the fidesapi Docker image.
	@echo ----
	@echo server-shell - Spins up the database, and starts a shell within a docker container with the local fidesapi files mounted.
	@echo ----
	@echo server-test - Run the tests for the fidesapi in a local docker container.
	@echo --------------------

####################
# Dev
####################

# CLI
cli: compose-build check-db
	@docker-compose run $(CLI_IMAGE_NAME)
	@make teardown

# Server
.PHONY: check-db
check-db: compose-build
	@echo "Check for new migrations to run..."
	@docker-compose down
	@docker-compose run $(SERVER_IMAGE_NAME) sbt flywayMigrate

.PHONY: init-db
init-db: compose-build
	@echo "Reset the db and run the migrations..."
	@docker-compose down
	@docker volume prune -f
	@docker-compose run $(SERVER_IMAGE_NAME) /bin/bash -c "sleep 10 && sbt flywayMigrate"
	@make teardown

.PHONY: server
server: check-db
	@echo "Spinning up the webserver..."
	@docker-compose up $(SERVER_IMAGE_NAME)
	@make teardown

.PHONY: shell
server-shell: check-db
	@echo "Setting up a local development shell... (press CTRL-D to exit)"
	@docker-compose run $(SERVER_IMAGE_NAME) /bin/bash
	@make teardown

####################
# Docker
####################

# CLI
cli-build:
	docker build --tag $(CLI_IMAGE) fidesctl/

cli-push: cli-build
	docker tag $(CLI_IMAGE) $(CLI_IMAGE_LATEST)
	docker push $(CLI_IMAGE)
	docker push $(CLI_IMAGE_LATEST)

# Server
server-build:
	docker build --tag $(SERVER_IMAGE) fidesapi/

server-push: server-build
	docker tag $(SERVER_IMAGE) $(SERVER_IMAGE_LATEST)
	docker push $(SERVER_IMAGE)
	docker push $(SERVER_IMAGE_LATEST)

####################
# CI
####################

# General
test-all: server-test fidesctl-check-all
	@echo "Running all tests and checks..."

# Fidesctl
fidesctl-check-all: fidesctl-check-install black pylint mypy xenon pytest
	@echo "Running formatter, linter, typechecker and tests..."

fidesctl-check-install:
	@echo "Checking that fidesctl is installed..."
	@docker-compose run $(CLI_IMAGE_NAME) \
	fidesctl

black: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	black --check src/
	
mypy: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	mypy --ignore-missing-imports src/

pylint: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	pylint src/

pytest: compose-build init-db
	@docker-compose up -d
	@docker-compose run $(CLI_IMAGE_NAME) \
	/bin/bash -c "sleep 90 & pytest"

xenon: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	xenon src \
	--max-absolute B \
	--max-modules A \
	--max-average A \
	--ignore "data, tests, docs" \
	--exclude "src/fidesctl/_version.py"

# Server
.PHONY: check
server-check:
	@echo "Checking project for style prior to commit..."
	# TODO: run your linters, formatters, and other commands here, e.g.
	@echo "Checks complete!"

.PHONY: test
server-test: compose-build init-db
	@echo "Running unit & integration tests..."
	@docker-compose run $(SERVER_IMAGE_NAME) sbt test

.PHONY: shell
server-package: compose-build
	@echo "Packaging the application..."
	@docker-compose run $(SERVER_IMAGE_NAME) sbt package

####################
# Utils
####################

.PHONY: clean
clean:
	@echo "Cleaning project temporary files and installed dependencies..."
	@docker system prune -f
	@docker-compose run $(SERVER_IMAGE_NAME) sbt clean cleanFiles
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
	@docker-compose up docs
