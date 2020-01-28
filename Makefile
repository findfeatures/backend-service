SHELL := /bin/bash

ALLURE_DIR ?= .allure
COVERAGE_DIR ?= .coverage-html

export ARGS

test: coverage check-coverage

static:
	pre-commit run --all-files

coverage:
	coverage run --concurrency=eventlet --source backend --branch -m pytest --alluredir=$(ALLURE_DIR) tests$(ARGS)
	coverage html -d $(COVERAGE_DIR)

check-coverage:
	coverage report -m --fail-under 100  --omit=backend/dependencies/send_grid/provider.py

run:
	nameko run --config config.yml backend.service:BackendService

build-image:
	docker build -t calumwebb/backend-service:$(TAG) .;

push-image:
	docker push calumwebb/backend-service:$(TAG)