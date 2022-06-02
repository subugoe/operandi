FROM python:latest

MAINTAINER OPERANDI

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LANG=C.UTF-8

WORKDIR /build-operandi
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
    
RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

WORKDIR /build-operandi/OPERANDI_TestRepo/src/priority_qeueu

RUN ./repo_setup.deb.sh	
RUN ./install.sh

CMD /bin/bash
