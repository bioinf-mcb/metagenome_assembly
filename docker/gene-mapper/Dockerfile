FROM ubuntu:20.04

# labels
LABEL ubuntu.version="20.04"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN mkdir /app

# set the working directory to /app
WORKDIR /app

# Installing needed dependencies
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y \
	python3 \
	python3-pip   

RUN python3 -m pip install click numpy pandas
RUN python3 -m pip install scikit-bio==0.5.6

# copy the script to the container
COPY genes_MAGS_eggNOG_mapping.py /app


