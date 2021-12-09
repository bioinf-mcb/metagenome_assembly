FROM ubuntu:18.04

RUN mkdir /app

WORKDIR /app

# Installing all dependancies
    RUN apt-get update && apt-get install -y \ 
            wget \
            python

# download eggnog-mapper v2.0.1 and uncompress in /app/eggnog-mapper-2.0.1/
RUN wget https://github.com/eggnogdb/eggnog-mapper/archive/2.0.1.tar.gz && \
        tar -xzf 2.0.1.tar.gz

# databases (>40G) not included in the docker image
# need to be downloaded or copied to /app/eggnog-mapper-2.0.1/data