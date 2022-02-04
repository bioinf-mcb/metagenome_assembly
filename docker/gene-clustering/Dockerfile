# $ docker build . -t gene_clustering:v1.0
# $ docker run --rm -it -v `pwd`:/data gene_clustering:latest /bin/bash
# TODO: update Bippython to a newest version
FROM biopython/biopython

COPY extract_complete_gene.py /app/extract_complete_gene.py

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
  cmake \
  && apt-get clean && apt-get purge \
  && mkdir /appdownload \
  && cd /appdownload

RUN wget https://www.drive5.com/downloads/usearch11.0.667_i86linux32.gz -P /app \
  && gunzip /app/usearch11.0.667_i86linux32.gz 

RUN cd /appdownload \
   && git clone https://github.com/weizhongli/cdhit.git \
   && cd cdhit \
   && make \
   && ln -s /appdownload/cdhit/cd-hit /app/cd-hit \
   && ln -s /appdownload/cdhit/cd-hit-est /app/cd-hit-est \
   && ln -s /appdownload/cdhit/cd-hit-est-2d /app/cd-hit-est-2d \
   && ln -s /appdownload/cdhit/cd-hit-2d /app/cd-hit-2d

ENV PATH /app:$PATH
RUN mv /biopython/Bio /app/ && chmod 755 /app/*

