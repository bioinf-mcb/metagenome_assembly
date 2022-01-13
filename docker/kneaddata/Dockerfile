FROM ubuntu:18.04

ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion

# install conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py37_4.10.3-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# Make RUN commands use `bash --login` (instead of '/bin/sh -c'):
SHELL ["/bin/bash", "--login", "-c"]

RUN conda init bash
RUN conda config --add channels defaults
RUN conda config --add channels bioconda
RUN conda config --add channels conda-forge
RUN conda config --add channels biobakery
RUN conda install kneaddata -c biobakery

RUN mkdir /hg37
COPY hg37dec_v0.1.1.bt2 /hg37/
COPY hg37dec_v0.1.2.bt2 /hg37/
COPY hg37dec_v0.1.3.bt2 /hg37/
COPY hg37dec_v0.1.4.bt2 /hg37/
COPY hg37dec_v0.1.rev.1.bt2 /hg37/
COPY hg37dec_v0.1.rev.2.bt2 /hg37/
