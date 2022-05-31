MAINTAINER OPERANDI

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LANG=C.UTF-8

WORKDIR /build-operandi
COPY src ./src
COPY tests ./tests
COPY README.md .
COPY OPERANDI_arch.png .
COPY requirements.txt .

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
    git \

RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

CMD /bin/bash
