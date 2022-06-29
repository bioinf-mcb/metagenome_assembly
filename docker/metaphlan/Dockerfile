# modified from https://github.com/biobakery/biobakery/blob/master/docker/metaphlan/Dockerfile
FROM ubuntu:20.04

ENV SAMTOOLS_VERSION=1.9 

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
    zip \
    libncurses5-dev \
    libbz2-dev \
    liblzma-dev 
    
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

# install samtools 
RUN mkdir samtools &&\
  cd samtools &&\
  wget https://github.com/samtools/samtools/releases/download/$SAMTOOLS_VERSION/samtools-$SAMTOOLS_VERSION.tar.bz2 &&\
  tar -xjf samtools-$SAMTOOLS_VERSION.tar.bz2 &&\
  rm samtools-$SAMTOOLS_VERSION.tar.bz2 &&\
  cd samtools-$SAMTOOLS_VERSION &&\
  ./configure &&\
  make &&\
  make install

WORKDIR /tmp