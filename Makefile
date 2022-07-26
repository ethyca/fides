.DEFAULT_GOAL := help

####################
# CONSTANTS
####################

REGISTRY := ethyca
IMAGE_TAG := $(shell git fetch --force --tags && git describe --tags --dirty --always)

# COMPOSE_SERVICE_NAME is webserver rather than fidesops_webserver because commands that don't
# use docker-compose fail with fidesops_webserver. When left as webserver here both
# sets of commands work.
COMPOSE_SERVICE_NAME := webserver
IMAGE_NAME := fidesops
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_LATEST := $(REGISTRY)/$(IMAGE_NAME):latest

DOCKERFILE_ENVIRONMENTS := postgres mysql mongodb mssql


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
	@docker-compose run --rm -e ANALYTICS_OPT_OUT $(COMPOSE_SERVICE_NAME) \
	python -c "\
	from fidesops.db.database import init_db; \
	from fidesops.core.config import config; \
	init_db(config.database.sqlalchemy_database_uri);"

reset-db:
	@echo "Resetting and re-initializing the application db..."
	@make teardown
	@docker volume rm fidesops_app-db-data || echo "No app DB found, continuing!"
	@make init-db

server: compose-build
	@docker-compose up

server-with-worker: compose-build
	@docker-compose up worker -d
	@docker-compose run \
	-e FIDESOPS__EXECUTION__WORKER_ENABLED=True \
	webserver

server-no-db: compose-build
	@docker-compose run \
	-e FIDESOPS__DATABASE__ENABLED=false \
    -e FIDESOPS__REDIS__ENABLED=false \
	--no-deps \
	--service-ports \
	webserver

server-shell: compose-build
	@docker-compose run $(COMPOSE_SERVICE_NAME) /bin/bash

integration-shell:
	@virtualenv -p python3 fidesops_test_dispatch; \
		source fidesops_test_dispatch/bin/activate; \
		python scripts/run_infrastructure.py --open_shell --datastores $(datastores)

integration-env:
	@virtualenv -p python3 fidesops_test_dispatch; \
		source fidesops_test_dispatch/bin/activate; \
		python scripts/run_infrastructure.py --run_application --datastores $(datastores)

quickstart:
	@virtualenv -p python3 fidesops_test_dispatch; \
		source fidesops_test_dispatch/bin/activate; \
		python scripts/run_infrastructure.py --datastores mongodb postgres --run_quickstart

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

check-all: isort-ci black-ci pylint mypy check-migrations pytest pytest-integration

black-ci: compose-build
	@echo "Running black checks..."
	@docker-compose run \
		-e ANALYTICS_OPT_OUT \
		$(COMPOSE_SERVICE_NAME) \
		black --check src/ tests/ \
		|| (echo "Error running 'black --check src/ tests/', please run 'make black' to format your code!"; exit 1)
	@make teardown

check-migrations: compose-build
	@echo "Check if there are unrun migrations..."
	@docker-compose run --rm -e ANALYTICS_OPT_OUT $(COMPOSE_SERVICE_NAME) \
	python -c "\
	from fidesops.db.database import check_missing_migrations; \
	from fidesops.core.config import config; \
	check_missing_migrations(config.database.sqlalchemy_database_uri);"
	@make teardown

isort-ci:
	@echo "Running isort checks..."
	@docker-compose run $(COMPOSE_SERVICE_NAME) \
		isort src tests --check-only

pylint: compose-build
	@echo "Running pylint checks..."
	@docker-compose run \
		-e ANALYTICS_OPT_OUT \
		$(COMPOSE_SERVICE_NAME) \
		pylint src/
	@make teardown

mypy: compose-build
	@echo "Running mypy checks..."
	@docker-compose run \
		-e ANALYTICS_OPT_OUT \
		$(COMPOSE_SERVICE_NAME) \
		mypy src/
	@make teardown

pytest: compose-build
	@echo "Running pytest unit tests..."
	@docker-compose run \
		-e ANALYTICS_OPT_OUT \
		$(COMPOSE_SERVICE_NAME) \
		pytest $(pytestpath) -m "not integration and not integration_external and not integration_saas"

	@make teardown

pytest-integration:
	@virtualenv -p python3 fidesops_test_dispatch; \
		source fidesops_test_dispatch/bin/activate; \
		python scripts/run_infrastructure.py --run_tests --analytics_opt_out --datastores $(datastores)
	@make teardown

# These tests connect to external third-party test databases
pytest-integration-external: compose-build
	@echo "Running tests that connect to external third party test databases"
	@docker-compose run \
		-e ANALYTICS_OPT_OUT \
		-e REDSHIFT_TEST_URI \
		-e SNOWFLAKE_TEST_URI -e REDSHIFT_TEST_DB_SCHEMA \
		-e BIGQUERY_KEYFILE_CREDS -e BIGQUERY_DATASET \
		$(COMPOSE_SERVICE_NAME) pytest $(pytestpath) -m "integration_external"
	@make teardown

pytest-saas: compose-build
	@echo "Running integration tests for SaaS connectors"
	@docker-compose run \
		-e ANALYTICS_OPT_OUT \
		-e VAULT_ADDR -e VAULT_NAMESPACE -e VAULT_TOKEN \
		$(COMPOSE_SERVICE_NAME) pytest $(pytestpath) -m "integration_saas"
	@make teardown


####################
# Utils
####################

.PHONY: black
black: compose-build
	@echo "Running black formatting against the src/ and tests/ directories..."
	@docker-compose run $(COMPOSE_SERVICE_NAME) black src/ tests/
	@make teardown
	@echo "Fin"

.PHONY: clean
clean:
	@echo "Cleaning project temporary files and installed dependencies..."
	@docker system prune -a --volumes
	@echo "Clean complete!"

.PHONY: compose-build
compose-build:
	@echo "Tearing down the docker compose images, network, etc..."
	@docker-compose down --remove-orphans
	@docker-compose build --build-arg SKIP_MSSQL_INSTALLATION="false"

.PHONY: isort
isort:
	@echo "Running isort checks..."
	@docker-compose run $(COMPOSE_SERVICE_NAME) \
		isort src tests

.PHONY: teardown
teardown:
	@echo "Tearing down the dev environment..."
	@docker-compose \
	-f docker-compose.yml \
	-f docker/docker-compose.integration-mariadb.yml \
	-f docker/docker-compose.integration-mongodb.yml \
	-f docker/docker-compose.integration-mssql.yml \
	-f docker/docker-compose.integration-mysql.yml \
	-f docker/docker-compose.integration-postgres.yml \
	down \
	--volumes \
	--remove-orphans
	@echo "Teardown complete"

.PHONY: docs-build
docs-build: compose-build
	@docker-compose run --rm $(COMPOSE_SERVICE_NAME) \
	python scripts/generate_openapi.py ./docs/fidesops/docs/api/openapi.json

.PHONY: docs-serve
docs-serve: docs-build
	@docker-compose build docs
	@docker-compose up docs


####################
# Test Data Creation
####################

user:
	@virtualenv -p python3 fidesops_test_dispatch; \
		source fidesops_test_dispatch/bin/activate; \
		python scripts/run_infrastructure.py --datastores postgres --run_create_superuser

test-data:
	@virtualenv -p python3 fidesops_test_dispatch; \
		source fidesops_test_dispatch/bin/activate; \
		python scripts/run_infrastructure.py --datastores postgres --run_create_test_data
