FROM ubuntu:18.04

ENV BWA_VERSION=0.7.17 SAMTOOLS_VERSION=1.9 

RUN apt-get update && apt-get install -y \
  make \
  wget \
  gcc \
  zlib1g-dev \
  bzip2 \
  libncurses5-dev \
  libbz2-dev \
  liblzma-dev \
  libcurl4-gnutls-dev \
  zlib1g-dev \
  libssl-dev \
  gcc \
  perl 

# install bwa
RUN mkdir bwa &&\
  mkdir /data &&\
  cd bwa &&\
  wget https://github.com/lh3/bwa/releases/download/v$BWA_VERSION/bwa-$BWA_VERSION.tar.bz2 &&\
  tar -xjf bwa-$BWA_VERSION.tar.bz2 &&\
  rm bwa-$BWA_VERSION.tar.bz2 &&\
  cd bwa-$BWA_VERSION &&\
  make

ENV PATH="${PATH}:/bwa/bwa-${BWA_VERSION}"

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

WORKDIR /data