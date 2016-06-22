DOCKERCOMPOSE = $(shell which docker-compose)

default:
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "dev-like environment:"
	@echo "   build      - build docker containers for dev"
	@echo "   run        - docker-compose up the entire system for dev"
	@echo ""
	@echo "Mozilla prod-like environment:"
	@echo "   build-prod - build docker containers for prod"
	@echo "   run-prod   - docker-compose up the entire system for prod"
	@echo ""
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "lint          - check style with flake8"
	@echo "test          - run tests"
	@echo "test-coverage - run tests and generate coverage report in cover/"
	@echo "docs          - generate Sphinx HTML documentation, including API docs"

# Prod configuration steps
.docker-build-prod:
	make build-prod

build-prod:
	${DOCKERCOMPOSE} -f docker-compose-prod.yml build
	touch .docker-build-prod

run-prod: .docker-build-prod
	${DOCKERCOMPOSE} -f docker-compose-prod.yml up

# Dev configuration steps
.docker-build:
	make build

build:
	${DOCKERCOMPOSE} build
	touch .docker-build

run: .docker-build
	${DOCKERCOMPOSE} up

clean:
	# container-built things
	${DOCKERCOMPOSE} run appbase rm -rf crashes
	${DOCKERCOMPOSE} run appbase rm -rf devcrashes

	# python related things
	-rm -fr build/
	-rm -fr dist/
	-rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

	# test related things
	-rm -f .coverage
	${DOCKERCOMPOSE} run appbase rm -fr cover

	# state files
	-rm .docker-build
	-rm .docker-build-prod

lint:
	${DOCKERCOMPOSE} run appbase flake8 collector

test:
	${DOCKERCOMPOSE} run appbase ./scripts/test.sh

test-coverage:
	${DOCKERCOMPOSE} run appbase ./scripts/test.sh --with-coverage --cover-package=collector --cover-html

docs:
	# FIXME: This might not work
	sphinx-apidoc -o docs/ collector
	$(MAKE) -C docs/ clean
	$(MAKE) -C docs/ html

.PHONY: default clean build docs lint run test test-coverage
