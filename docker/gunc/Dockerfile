FROM ubuntu:20.04

RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y python3 \
    python3-dev \
    python3-pip \
    apt-transport-https \
    wget \
    git 

RUN pip3 install gunc 