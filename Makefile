.DEFAULT_GOAL := help

####################
# CONSTANTS
####################

REGISTRY := ethyca
# If running in CI, inherit the SHA; otherwise, calculate it from git
GIT_COMMIT_SHA ?= $(CI_COMMIT_SHORT_SHA)
ifeq ($(strip $(GIT_COMMIT_SHA)),)
GIT_COMMIT_SHA := $(shell git rev-parse --short HEAD)
endif
IMAGE_TAG := $(GIT_COMMIT_SHA)

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
	@echo "Available targets:"
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'
####################
# Dev
####################

# CLI
cli: compose-build check-db
	@docker-compose run $(CLI_IMAGE_NAME)

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

.PHONY: server
server: check-db
	@echo "Spinning up the webserver..."
	@docker-compose up $(SERVER_IMAGE_NAME)
	@echo "Exited webserver, tearing down environment..."
	@docker-compose down
	@echo "Teardown complete!"

.PHONY: shell
server-shell: check-db
	@echo "Setting up a local development shell... (press CTRL-D to exit)"
	@docker-compose run $(SERVER_IMAGE_NAME) /bin/bash
	@echo "Exited development shell, tearing down environment..."
	@docker-compose down
	@echo "Teardown complete!"

####################
# Docker
####################

# CLI
cli-build:
	@echo "Building the $(CLI_IMAGE) image..."
	docker build --tag $(CLI_IMAGE) fidesctl/

cli-push: cli-build
	@echo "Pushing the $(CLI_IMAGE) image to $(DOCKER_REGISTRY)..."
	docker tag $(CLI_IMAGE) $(CLI_IMAGE_LATEST)
	docker push $(CLI_IMAGE)
	docker push $(CLI_IMAGE_LATEST)

# Server
server-build:
	@echo "Building the $(SERVER_IMAGE) image..."
	docker build --tag $(SERVER_IMAGE) fidesapi/

server-push: server-build
	@echo "Pushing the $(SERVER_IMAGE) image to $(DOCKER_REGISTRY)..."
	docker tag $(SERVER_IMAGE) $(SERVER_IMAGE_LATEST)
	docker push $(SERVER_IMAGE)
	docker push $(SERVER_IMAGE_LATEST)

####################
# CI
####################

# General
test-all: server-test cli-check-all
	@echo "Running all tests and checks..."

# CLI
cli-check: black pylint mypy pytest
	@echo "Running formatter, linter, typechecker and tests..."

black: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	black src/

pylint: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	pylint src/

pytest: compose-build init-db
	@docker-compose up -d
	@docker-compose run $(CLI_IMAGE_NAME) \
	/bin/bash -c "sleep 90 & pytest"

mypy: compose-build
	@docker-compose run $(CLI_IMAGE_NAME) \
	mypy --ignore-missing-imports src/

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

.PHONY: compose-build
compose-build:
	@echo "Build the images required in the docker-compose file..."
	@docker-compose down
	@docker-compose build

.PHONY: docs-serve
docs-serve:
	@docker-compose up docs
