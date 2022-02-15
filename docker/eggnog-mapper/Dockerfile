FROM ubuntu:20.04

RUN mkdir /app

WORKDIR /app

# Installing all dependancies
    RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y \ 
            build-essential \
            wget \
            python3.9 \
            python3.9-dev \
            python3-setuptools 

# download eggnog-mapper v2.1.6 and uncompress in /app/eggnog-mapper-2.1.6/
RUN wget https://github.com/eggnogdb/eggnog-mapper/archive/refs/tags/2.1.6.tar.gz \
        && tar -xzf 2.1.6.tar.gz \
        && cd eggnog-mapper-2.1.6 \
        && python3.9 setup.py install \
        && rm -rf 2.1.6.tar.gz