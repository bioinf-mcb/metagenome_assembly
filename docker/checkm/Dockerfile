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
        libjpeg-dev


# prodigal
RUN mkdir /checkm-deps && \
    cd /checkm-deps && wget https://github.com/hyattpd/Prodigal/releases/download/v2.6.3/prodigal.linux && \
    mv prodigal.linux /usr/local/bin/prodigal && chmod 755 /usr/local/bin/prodigal

# hmmer
RUN cd /checkm-deps && wget http://eddylab.org/software/hmmer3/3.1b2/hmmer-3.1b2-linux-intel-x86_64.tar.gz && \
    tar -xvzf hmmer-3.1b2-linux-intel-x86_64.tar.gz && \
    cd hmmer-3.1b2-linux-intel-x86_64 && ./configure &&  \
    make && make install

# pplacer
RUN cd /checkm-deps && wget https://github.com/matsen/pplacer/releases/download/v1.1.alpha19/pplacer-linux-v1.1.alpha19.zip && \
    unzip pplacer-linux-v1.1.alpha19.zip && \
    cp pplacer-Linux-v1.1.alpha19/pplacer /usr/local/bin/ && \
    cp pplacer-Linux-v1.1.alpha19/guppy /usr/local/bin/ && \
    cp pplacer-Linux-v1.1.alpha19/rppr /usr/local/bin/

# checkm 
RUN pip3 install \
    numpy \
    matplotlib \
    pysam \
    checkm-genome

## checkm data 
RUN cd / && mkdir checkm-data && cd checkm-data \
    && wget https://data.ace.uq.edu.au/public/CheckM_databases/checkm_data_2015_01_16.tar.gz \
    && tar -xvzf checkm_data_2015_01_16.tar.gz 

RUN echo checkm-data | checkm data setRoot /checkm-data
