export

SHELL = /bin/bash
PYTHON = python
PIP3 = pip3
PIP3_INSTALL = pip3 install

DB_NAME='operandi_db'
DB_URL='mongodb://localhost:27018'
RABBITMQ_URL='localhost:5672'
BASE_DIR='/tmp/operandi_data'

TEST_DB_NAME='test_operandi_db'
# TEST_DB_URL='mongodb://141.5.99.32:27018'
TEST_DB_URL='mongodb://localhost:27018'
# TEST_RABBITMQ_URL='141.5.99.32:5672'
TEST_RABBITMQ_URL='localhost:5672'
TEST_BASE_DIR='/tmp/operandi_tests'

OPERANDI_USERNAME='test'
OPERANDI_PASSWORD='test'

BUILD_ORDER = src/utils src/server src/broker src/harvester
UNINSTALL_ORDER = operandi_harvester operandi_broker operandi_server operandi_utils

help:
	@echo ""
	@echo "Targets"
	@echo " deps-ubuntu             Dependencies for deployment in an ubuntu/debian linux"
	@echo " deps-test               Install test python deps via pip"
	@echo " install                 (Re)install the modules"
	@echo " install-dev             Install with pip install -e"
	@echo " uninstall               Uninstall the modules"
	@echo ""
	@echo " start-mongo-docker      Start the dockerized MongoDB"
	@echo " start-rabbitmq-docker   Start the dockerized RabbitMQ Server"
	@echo " start-broker-docker     Start the dockerized Operandi Broker"
	@echo " start-server-docker     Start the dockerized Operandi Server"
	@echo ""
	@echo " start-broker-native     Start the native Operandi Broker"
	@echo " start-server-native     Start the native Operandi Server"
	@echo " start-harvester-native  Start the native Operandi Harvester"
	@echo ""
	@echo " start-all-modules       Start all image based docker modules"
	@echo " stop-all-modules        Stop all image based docker modules"
	@echo " clean-all-modules       Clean all image based docker modules"
	@echo ""
	@echo " In order to run the tests, MongoDB must be running on port 27018"
	@echo ""
	@echo " run-tests               Run all tests"
	@echo " run-tests-broker        Run all broker tests"
	@echo " run-tests-harvester     Run all harvester tests"
	@echo " run-tests-server        Run all server tests"
	@echo " run-tests-utils         Run all utils tests"
	@echo ""


# Dependencies for deployment in an ubuntu/debian linux
deps-ubuntu:
	apt-get install -y python3 python3-venv python3-pip

# Install test python deps via pip
deps-test:
	$(PIP3) install -U pip
	$(PIP3) install -r requirements_test.txt

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

start-all-modules:
	docker compose -f ./docker-compose_image_based.yml up -d

stop-all-modules:
	docker compose -f ./docker-compose_image_based.yml down --remove-orphans

clean-all-modules:
	docker rmi -f ghcr.io/subugoe/operandi-server:main
	docker rmi -f ghcr.io/subugoe/operandi-broker:main

start-mongo-docker:
	docker compose -f ./docker-compose.yml up -d operandi-mongodb

start-rabbitmq-docker:
	docker compose -f ./docker-compose.yml up -d operandi-rabbitmq

start-broker-docker:
	docker compose -f ./docker-compose.yml up -d operandi-broker

start-server-docker:
	docker compose -f ./docker-compose.yml up -d operandi-server

start-broker-native:
	OPERANDI_URL_RABBITMQ_SERVER=$(RABBITMQ_URL) \
	OCRD_WEBAPI_DB_URL=$(DB_URL) \
	OCRD_WEBAPI_DB_NAME=$(DB_NAME) \
	OCRD_WEBAPI_BASE_DIR=$(BASE_DIR) \
	operandi-broker start

start-server-native:
	OPERANDI_URL_RABBITMQ_SERVER=$(RABBITMQ_URL) \
	OCRD_WEBAPI_DB_URL=$(DB_URL) \
	OCRD_WEBAPI_DB_NAME=$(DB_NAME) \
	OCRD_WEBAPI_BASE_DIR=$(BASE_DIR) \
	operandi-server start

start-harvester-native:
	operandi-harvester start-dummy --address http://localhost:8000

run-tests: run-tests-server run-tests-broker run-tests-utils run-tests-harvester

run-tests-broker:
	OPERANDI_URL_RABBITMQ_SERVER=$(TEST_RABBITMQ_URL) \
	OPERANDI_TESTS_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_BASE_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_DB_NAME=$(TEST_DB_NAME) \
	OCRD_WEBAPI_DB_URL=$(TEST_DB_URL) \
	OCRD_WEBAPI_USERNAME=$(OPERANDI_USERNAME) \
	OCRD_WEBAPI_PASSWORD=$(OPERANDI_PASSWORD) \
	pytest tests/broker/test_*.py

run-tests-harvester:
	OPERANDI_URL_RABBITMQ_SERVER=$(TEST_RABBITMQ_URL) \
	OPERANDI_TESTS_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_BASE_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_DB_NAME=$(TEST_DB_NAME) \
	OCRD_WEBAPI_DB_URL=$(TEST_DB_URL) \
	OCRD_WEBAPI_USERNAME=$(OPERANDI_USERNAME) \
	OCRD_WEBAPI_PASSWORD=$(OPERANDI_PASSWORD) \
	pytest tests/harvester/test_*.py

run-tests-server:
	OPERANDI_URL_RABBITMQ_SERVER=$(TEST_RABBITMQ_URL) \
	OPERANDI_TESTS_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_BASE_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_DB_NAME=$(TEST_DB_NAME) \
	OCRD_WEBAPI_DB_URL=$(TEST_DB_URL) \
	OCRD_WEBAPI_USERNAME=$(OPERANDI_USERNAME) \
	OCRD_WEBAPI_PASSWORD=$(OPERANDI_PASSWORD) \
	pytest tests/server/test_*.py

run-tests-utils:
	OPERANDI_URL_RABBITMQ_SERVER=$(TEST_RABBITMQ_URL) \
	OPERANDI_TESTS_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_BASE_DIR=$(TEST_BASE_DIR) \
	OCRD_WEBAPI_DB_NAME=$(TEST_DB_NAME) \
	OCRD_WEBAPI_DB_URL=$(TEST_DB_URL) \
	OCRD_WEBAPI_USERNAME=$(OPERANDI_USERNAME) \
	OCRD_WEBAPI_PASSWORD=$(OPERANDI_PASSWORD) \
	pytest tests/utils/test_*.py

pyclean:
	rm -f **/*.pyc
	find . -name '__pycache__' -exec rm -rf '{}' \;
	rm -rf .pytest_cache
