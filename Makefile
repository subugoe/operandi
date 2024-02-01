SHELL = /bin/bash
PYTHON = python
PIP3 = pip3
PIP3_INSTALL = pip3 install

BUILD_ORDER = src/utils src/server src/broker src/harvester
UNINSTALL_ORDER = operandi_harvester operandi_broker operandi_server operandi_utils

ifneq (,$(wildcard ./.env))
    include ./.env
endif

ifneq (,$(wildcard ./tests/.env))
    include ./tests/.env
endif

help:
	@echo ""
	@echo "Targets"
	@echo " deps-ubuntu             Dependencies for deployment in an ubuntu/debian linux"
	@echo " deps-test               Install test python deps via pip"
	@echo " install                 (Re)install the modules"
	@echo " install-dev             Install with pip install -e"
	@echo " uninstall               Uninstall the modules"
	@echo ""
	@echo " start-broker-native     Start the native Operandi Broker"
	@echo " start-server-native     Start the native Operandi Server"
	@echo " start-harvester-dummy   Start the native Operandi Harvester with a dummy 1 cycle"
	@echo ""
	@echo " USED ONLY FOR RUNNING THE TESTS "
	@echo " start-mongo-docker      Start the dockerized MongoDB"
	@echo " start-rabbitmq-docker   Start the dockerized RabbitMQ Server"
	@echo ""
	@echo " start-all-docker-modules       Start all docker modules from local"
	@echo " stop-all-docker-modules        Stop all docker modules from local"
	@echo " clean-all-docker-modules       Clean all docker modules from local"
	@echo ""
	@echo " start-all-image-based-docker-modules       Start all docker modules from repo images"
	@echo " stop-all-image-based-docker-modules        Stop all docker modules from repo image"
	@echo " clean-all-image-based-docker-modules       Clean all docker modules from repo images"
	@echo ""
	@echo " In order to run the tests, MongoDB must be running on port 27018"
	@echo " In order to run the tests, RabbitMQ Server must be running on port 5672"
	@echo ""
	@echo " run-tests               Run all tests"
	@echo " run-tests-broker        Run all broker tests"
	@echo " run-tests-harvester     Run all harvester tests"
	@echo " run-tests-server        Run all server tests"
	@echo " run-tests-utils         Run all utils tests"
	@echo " run-tests-integration   Run the integration test"
	@echo ""


# Dependencies for deployment in an ubuntu/debian linux
deps-ubuntu:
	apt-get install -y python3 python3-venv python3-pip

# Install test python deps via pip
deps-test:
	$(PIP3) install -U pip
	$(PIP3) install -r tests/requirements.txt

# (Re)install the tool
install:
	$(PIP3) install -U pip wheel
	for mod in $(BUILD_ORDER);do (cd $$mod ; $(PIP3_INSTALL) .);done

# Install with pip install -e
install-dev: uninstall
	$(MAKE) install PIP3_INSTALL="pip install -e"

# Uninstall the tool
uninstall:
	for mod in $(UNINSTALL_ORDER);do $(PIP3) uninstall -y $$mod;done

start-all-image-based-docker-modules:
	docker compose -f ./docker-compose_image_based.yml --env-file docker.env up -d

stop-all-image-based-docker-modules:
	docker compose -f ./docker-compose_image_based.yml --env-file docker.env down --remove-orphans

clean-all-image-based-docker-modules:
	docker rmi -f ghcr.io/subugoe/operandi-server:main
	docker rmi -f ghcr.io/subugoe/operandi-broker:main

start-all-docker-modules:
	docker compose -f ./docker-compose.yml --env-file docker.env up -d

stop-all-docker-modules:
	docker compose -f ./docker-compose.yml --env-file docker.env down --remove-orphans

clean-all-docker-modules:
	docker rmi -f operandi-broker:latest
	docker rmi -f operandi-server:latest

start-mongo-docker:
	docker compose -f ./docker-compose.yml --env-file .env up -d operandi-mongodb

start-rabbitmq-docker:
	docker compose -f ./docker-compose.yml --env-file .env up -d operandi-rabbitmq

start-broker-native:
	export $(shell sed 's/=.*//' ./.env)
	operandi-broker start

start-server-native:
	export $(shell sed 's/=.*//' ./.env)
	operandi-server start

start-harvester-dummy:
	export $(shell sed 's/=.*//' ./.env)
	operandi-harvester start-dummy --address http://localhost

run-tests:  run-tests-server run-tests-harvester run-tests-broker run-tests-utils run-tests-integration

run-tests-broker:
	export $(shell sed 's/=.*//' ./tests/.env)
	pytest tests/tests_broker/test_*.py -v

run-tests-harvester:
	export $(shell sed 's/=.*//' ./tests/.env)
	pytest tests/tests_harvester/test_*.py -v

run-tests-server:
	export $(shell sed 's/=.*//' ./tests/.env)
	pytest tests/tests_server/test_*.py -v

run-tests-utils:
	export $(shell sed 's/=.*//' ./tests/.env)
	pytest tests/tests_utils/test_*.py -v

run-tests-integration:
	export $(shell sed 's/=.*//' ./tests/.env)
	pytest tests/integration_tests/test_*.py -v

pyclean:
	rm -f **/*.pyc
	find . -name '__pycache__' -exec rm -rf '{}' \;
	rm -rf .pytest_cache
