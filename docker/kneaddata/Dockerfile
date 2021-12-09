# $ docker build . -t gene_clustering:v1.0
# $ docker run --rm -it -v `pwd`:/data gene_clustering:latest /bin/bash

FROM biopython/biopython

RUN mkdir /app && mkdir /appdownload

WORKDIR /appdownload

COPY usearch8.1.1861_i86linux64 /app
COPY extract_complete_gene.py /app

RUN apt-get update && apt-get install -y \
  curl \
  git \
  wget \
  mercurial \
  unzip \
  bzip2 \
  make \
  gcc \
  g++ \
  libncurses5-dev \
  zlib1g-dev \
  liblzma-dev \
  libtbb-dev \
  pigz \
  cmake

RUN git clone https://github.com/weizhongli/cdhit.git \
   && cd cdhit \
   && make \
   && ln -s /appdownload/cdhit/cd-hit /app/cd-hit \
   && ln -s /appdownload/cdhit/cd-hit-est /app/cd-hit-est \
   && ln -s /appdownload/cdhit/cd-hit-est-2d /app/cd-hit-est-2d \
   && ln -s /appdownload/cdhit/cd-hit-2d /app/cd-hit-2d

ENV PATH /app:$PATH
RUN chmod 755 /app/*

