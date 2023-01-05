export

SHELL = /bin/bash
PYTHON = python
PIP3 = pip3
PIP3_INSTALL = pip3 install
TESTDIR = tests

BUILD_ORDER = src/rabbit_mq_utils src/operandi_server src/service_broker src/harvester
UNINSTALL_ORDER = rabbit_mq_utils operandi_server service_broker harvester

# BEGIN-EVAL makefile-parser --make-help Makefile
  # TODO: "    test           Run all unit tests"
  # TODO: "    docs           Build documentation"
  # TODO: "    docs-clean     Clean docs"
  # TODO: "    docs-coverage  Calculate docstring coverage"
  
help:
	@echo ""
	@echo "Targets"
	@echo " deps-ubuntu             Dependencies for deployment in an ubuntu/debian linux"
	@echo " deps-test               Install test python deps via pip"
	@echo " install                 (Re)install the modules"
	@echo " install-dev             Install with pip install -e"
	@echo " uninstall               Uninstall the modules"
	@echo ""
	@echo " start-mongo             Start the Mongo DB docker container"
	@echo " start-rabbitmq          Start the RabbitMQ Server docker container"
	@echo " start-broker-hpc        Start the Operandi Broker locally for hpc (workflows executed in HPC)"
	@echo " start-broker-local      Start the Operandi Broker locally for local (workflows executed locally)"
	@echo " start-harvester         Start the Operandi Harvester"
	@echo " start-server            Start the Operandi Server"
	@echo ""

# END-EVAL

# Docker tags - used previously, not used currently
# Left for reference before we have a working docker registry
DOCKER_ALL = operandi-all-in-one
DOCKER_HARVESTER = operandi-harvester
DOCKER_SERVER = operandi-server
DOCKER_BROKER = operandi-service-broker

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
	# Uninstall ocr-d webapi to force pulling the newest version
	$(PIP3) uninstall -y ocrd_webapi


start-mongo:
	docker-compose up -d operandi-mongodb

start-rabbitmq:
	docker-compose up -d operandi-rabbit-mq

start-broker-hpc:
	operandi-broker start

start-broker-local:
	operandi-broker start --mocked

start-server:
	operandi-server start

start-harvester:
	operandi-harvester start --limit 1

pyclean:
	rm -f **/*.pyc
	find . -name '__pycache__' -exec rm -rf '{}' \;
	rm -rf .pytest_cache
