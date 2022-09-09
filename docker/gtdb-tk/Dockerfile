FROM ubuntu:18.04

# Installing all dependancies
RUN apt-get update && apt-get install -y \ 
        unzip \ 
        make \
        wget \ 
        build-essential \
        python3 \
        python3-pip \
        cython3 \
        zlib1g-dev \
        libbz2-dev \
        liblzma-dev \
        libjpeg-dev \
        jq

# prodigal
RUN mkdir /gtdb-deps && \
    cd /gtdb-deps && wget https://github.com/hyattpd/Prodigal/releases/download/v2.6.3/prodigal.linux && \
    mv prodigal.linux /usr/local/bin/prodigal && chmod 755 /usr/local/bin/prodigal
# hmmer
RUN cd /gtdb-deps && wget http://eddylab.org/software/hmmer3/3.1b2/hmmer-3.1b2-linux-intel-x86_64.tar.gz && \
    tar -xvzf hmmer-3.1b2-linux-intel-x86_64.tar.gz && \
    cd hmmer-3.1b2-linux-intel-x86_64 && ./configure &&  \
    make && make install
# pplacer
RUN cd /gtdb-deps && wget https://github.com/matsen/pplacer/releases/download/v1.1.alpha19/pplacer-linux-v1.1.alpha19.zip && \
    unzip pplacer-linux-v1.1.alpha19.zip && \
    cp pplacer-Linux-v1.1.alpha19/pplacer /usr/local/bin/ && \
    cp pplacer-Linux-v1.1.alpha19/guppy /usr/local/bin/ && \
    cp pplacer-Linux-v1.1.alpha19/rppr /usr/local/bin/
# fastANI
RUN cd /gtdb-deps && wget https://github.com/ParBLiSS/FastANI/releases/download/v1.3/fastANI-Linux64-v1.3.zip && \
    unzip fastANI-Linux64-v1.3.zip && \
    mv fastANI /usr/local/bin/
# FastTree
RUN cd /gtdb-deps && wget http://www.microbesonline.org/fasttree/FastTree && \
    chmod 755 FastTree && \
    mv FastTree /usr/local/bin/ && \
    wget http://www.microbesonline.org/fasttree/FastTreeMP && \
    chmod 755 FastTreeMP && \
    mv FastTreeMP /usr/local/bin/ 

# GTDB-Tk 
COPY config.json /gtdb-deps
RUN export GTDBTK_VERSION=$(jq -r ".gtdbtk_version" /gtdb-deps/config.json) && \
    pip3 install numpy && pip3 install matplotlib && pip3 install pysam && pip3 install gtdbtk==$GTDBTK_VERSION

## GTDB-Tk data 
RUN mkdir /gtdbtk-data  
ARG GTDBTK_DATA_PATH=/gtdbtk-data/
## This data needs to be obtained before analysis (not included in the docker image)

