# modified from https://github.com/biobakery/biobakery/blob/master/docker/metaphlan/Dockerfile
FROM ubuntu:20.04

# also install python version 2 used by bowtie2
RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y python3 \
    python3-dev \
    python3-pip \
    apt-transport-https \
    openjdk-8-jre \
    wget \
    git \
    libtbb-dev \
    bowtie2 \
    zip
    
RUN pip3 install boto3 \ 
    cloudpickle \
    awscli \
    numpy \
    cython \
    biom-format 

# install cmseq
RUN git clone https://github.com/SegataLab/cmseq.git \
    && cd cmseq  \
    && python3 setup.py install  \
    && cd ../  \
    && rm -r cmseq

RUN pip3 install metaphlan==3.0.14 && metaphlan --install

WORKDIR /tmp