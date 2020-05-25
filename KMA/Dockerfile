FROM ubuntu:18.04

# labels
LABEL ubuntu.version="18.04"
LABEL software="kma"
LABEL software.version="1.2.26"
LABEL description="K-mer alignment"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN mkdir /app

WORKDIR /app

# install dependencies
RUN apt-get update -y && apt-get install -y \
	gcc \
	libz-dev \
	make \
	git

RUN git clone https://bitbucket.org/genomicepidemiology/kma.git && \
	cd kma && \
	make

ENV PATH="$PATH:/app/kma"

CMD ["bash"]
