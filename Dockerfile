FROM ubuntu:22.04 as operandi_base

MAINTAINER OPERANDI
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /build-operandi

COPY src ./src
COPY Makefile .

RUN apt-get update && apt-get install -y \
    curl \
    git  \
    make \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    software-properties-common \
    sudo \
    time \
    wget

RUN python3 -m pip install --upgrade pip setuptools
RUN pip3 install -U pip wheel

RUN python3 -m pip install -r /build-operandi/src/utils/requirements.txt --ignore-installed
RUN pip3 install /build-operandi/src/utils

RUN python3 -m pip install -r /build-operandi/src/broker/requirements.txt --ignore-installed
RUN pip3 install /build-operandi/src/broker

RUN python3 -m pip install -r /build-operandi/src/harvester/requirements.txt --ignore-installed
RUN pip3 install /build-operandi/src/harvester

RUN python3 -m pip install -r /build-operandi/src/server/requirements.txt --ignore-installed
RUN pip3 install /build-operandi/src/server

RUN mkdir /operandi-data && chmod 777 /operandi-data
RUN mkdir /operandi-logs && chmod 777 /operandi-logs

RUN echo "Operandi build success"
RUN operandi-broker --version
RUN operandi-server --version
RUN operandi-harvester --version

FROM operandi_base as operandi_tests
WORKDIR /build-operandi
COPY Makefile .
COPY tests ./tests
RUN python3 -m pip install -r ./tests/requirements.txt

CMD ["yes"]
