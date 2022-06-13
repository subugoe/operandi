ARG BASE_IMAGE
FROM $BASE_IMAGE

MAINTAINER OPERANDI
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /OPERANDI_TestRepo
COPY . .
RUN chmod -R 765 .

RUN apt-get update
RUN apt-get -y install \
    ca-certificates \
    software-properties-common \
    python3-dev \
    python3-pip \
    make \
    wget \
    time \
    curl \
    sudo \
    git

RUN make deps-ubuntu
RUN python3 -m pip install --upgrade pip setuptools 
RUN python3 -m pip install -r requirements_test.txt
RUN make install 

# Install the RabbitMQ Server
# This is not needed in docker, we will use RabbitMQ docker instance
RUN ./src/priority_queue/repo_setup.deb.sh	
RUN ./src/priority_queue/install.sh

# No entry point for the docker image
CMD /bin/bash
