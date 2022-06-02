FROM python:latest

MAINTAINER OPERANDI

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
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
    
RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

RUN ./src/priority_queue/repo_setup.deb.sh	
RUN ./src/priority_queue/install.sh

CMD /bin/bash
