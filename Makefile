export

# This Makefile is based on the Makefile of OCR-D
# https://github.com/OCR-D/core/blob/master/Makefile

SHELL = /bin/bash
PYTHON = python
PIP = pip
PYTHONIOENCODING=utf8
TESTDIR = tests

BUILD_ORDER = src/priority_queue src/operandi_server src/service_broker src/harvester

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    deps-ubuntu    Dependencies for deployment in an ubuntu/debian linux"
	@echo "    deps-test      Install test python deps via pip"
	@echo "    install        (Re)install the modules"
	@echo "    install-dev    Install with pip install -e"
	@echo "    uninstall      Uninstall the modules"

	# TODO: @echo "    test           Run all unit tests"
	# TODO: @echo "    docs           Build documentation"
	# TODO: @echo "    docs-clean     Clean docs"
	# TODO: @echo "    docs-coverage  Calculate docstring coverage"
	@echo "    docker         Build docker image"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    DOCKER_TAG         Docker tag. Default: '$(DOCKER_TAG)'."
	@echo "    DOCKER_BASE_IMAGE  Docker base image. Default: '$(DOCKER_BASE_IMAGE)'."
	@echo "    DOCKER_ARGS        Additional arguments to docker build. Default: '$(DOCKER_ARGS)'"
	@echo "    PIP_INSTALL        pip install command. Default: $(PIP_INSTALL)"

# END-EVAL

# Docker tag. Default: '$(DOCKER_TAG)'.
DOCKER_TAG = operandi-test-1.0

# Docker base image. Default: '$(DOCKER_BASE_IMAGE)'.
DOCKER_BASE_IMAGE = ubuntu:18.04

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
	for mod in $(BUILD_ORDER);do pip uninstall -y $$mod;done

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

.PHONY: docker

# Build docker image
docker:
	docker build -t $(DOCKER_TAG) --build-arg BASE_IMAGE=$(DOCKER_BASE_IMAGE) $(DOCKER_ARGS) .
