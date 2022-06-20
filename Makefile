export

# This Makefile is based on the Makefile of OCR-D
# https://github.com/OCR-D/core/blob/master/Makefile

SHELL = /bin/bash
PYTHON = python
PIP = pip
PYTHONIOENCODING=utf8
TESTDIR = tests

BUILD_ORDER = src/priority_queue src/operandi_server src/service_broker src/harvester
UNINSTALL_ORDER = priority_queue operandi_server service_broker harvester

# BEGIN-EVAL makefile-parser --make-help Makefile

  # TODO: "    test           Run all unit tests"
  # TODO: "    docs           Build documentation"
  # TODO: "    docs-clean     Clean docs"
  # TODO: "    docs-coverage  Calculate docstring coverage"
  
help:
	@echo ""
	@echo "Targets"
	@echo ""
	@echo " deps-ubuntu             Dependencies for deployment in an ubuntu/debian linux"
	@echo " deps-test               Install test python deps via pip"
	@echo " install                 (Re)install the modules"
	@echo " install-dev             Install with pip install -e"
	@echo " uninstall               Uninstall the modules"
	@echo " docker-all              Build everything in a single docker image"
	@echo " docker-harvester        Build harvester docker image"
	@echo " docker-server           Build server docker image"
	@echo " docker-broker           Build service-broker docker image"
	@echo ""
	@echo "Variables"
	@echo ""
	@echo " DOCKER_ALL              Docker all tag: '${DOCKER_ALL}'"
	@echo " DOCKER_HARVESTER        Docker harvester tag: '${DOCKER_HARVESTER}'"
	@echo " DOCKER_SERVER           Docker server tag: '${DOCKER_SERVER}'"
	@echo " DOCKER_BROKER           Docker broker tag: '${DOCKER_BROKER}'"
	@echo " DOCKER_UBUNTU_IMAGE     Docker ubuntu image: '${DOCKER_UBUNTU_IMAGE}'"
	@echo " DOCKER_PYTHON_IMAGE     Docker python image: '${DOCKER_PYTHON_IMAGE}'"
	@echo " DOCKER_ARGS             Additional arguments to docker build: '$(DOCKER_ARGS)'"
	@echo " PIP_INSTALL             pip install command. Default: $(PIP_INSTALL)"

# END-EVAL

# Docker tags
DOCKER_ALL = operandi-all-in-one
DOCKER_HARVESTER = operandi-harvester
DOCKER_SERVER = operandi-server
DOCKER_BROKER = operandi-service-broker

# Docker images
DOCKER_UBUNTU_IMAGE = ubuntu:18.04
DOCKER_PYTHON_IMAGE = python:3.9

# Additional arguments to docker build. Default: '$(DOCKER_ARGS)'
DOCKER_ARGS = 

# pip install command. Default: $(PIP_INSTALL)
PIP_INSTALL = pip install


# Dependencies for deployment in an ubuntu/debian linux
deps-ubuntu:
	apt-get install -y python3 python3-venv

# Install test python deps via pip
deps-test:
	$(PIP) install -U pip
	$(PIP) install -r requirements_test.txt

# (Re)install the tool
install:
	$(PIP) install -U pip wheel
	for mod in $(BUILD_ORDER);do (cd $$mod ; $(PIP_INSTALL) .);done

# Install with pip install -e
install-dev: uninstall
	$(MAKE) install PIP_INSTALL="pip install -e"

# Uninstall the tool
uninstall:
	for mod in $(UNINSTALL_ORDER);do pip uninstall -y $$mod;done

#
# Tests
#
# TODO: To be added

#
# Documentation
#
# TODO: To be added

#
# Clean up
#

pyclean:
	rm -f **/*.pyc
	find . -name '__pycache__' -exec rm -rf '{}' \;
	rm -rf .pytest_cache

#
# Docker
#

.PHONY: docker-all docker-harvester docker-server docker-broker

# Build docker image all-in-one by default
docker-all:
	docker build -t $(DOCKER_ALL) --build-arg BASE_IMAGE=$(DOCKER_UBUNTU_IMAGE) $(DOCKER_ARGS) .
	# docker build -t operandi-all-in-one --build-arg BASE_IMAGE=ubuntu:18.04 $(DOCKER_ARGS) .

# For separate docker builds
docker-harvester: 
	docker build -t $(DOCKER_HARVESTER) --build-arg BASE_IMAGE=$(DOCKER_UBUNTU_IMAGE) $(DOCKER_ARGS) ./src/harvester/

docker-server: 
	docker build -t $(DOCKER_SERVER) --build-arg BASE_IMAGE=$(DOCKER_UBUNTU_IMAGE) $(DOCKER_ARGS) ./src/operandi_server/

docker-broker: 
	docker build -t $(DOCKER_BROKER) --build-arg BASE_IMAGE=$(DOCKER_UBUNTU_IMAGE) $(DOCKER_ARGS) ./src/service_broker/