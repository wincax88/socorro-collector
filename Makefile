default:
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "install - install the package to the active Python's site-packages"

build:
	docker-compose build

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	
	rm -f .coverage
	rm -fr htmlcov/

lint:
	flake8 collector tests

docs:
	sphinx-apidoc -o docs/ collector
	$(MAKE) -C docs/ clean
	$(MAKE) -C docs/ html

run:
	docker-compose up

.PHONY: default clean build docs test
