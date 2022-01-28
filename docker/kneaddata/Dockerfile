FROM ubuntu:20.04
# tzdata installation
ARG DEBIAN_FRONTEND=noninteractive

ENV APPS_HOME=/app APPS_DOWN=/appdownload TRIMMOMATIC_V=0.39 BOWTIE_V=2.4.5 TZ=Europe

RUN mkdir $APPS_HOME && mkdir $APPS_DOWN && cd $APPS_DOWN

RUN apt-get update && apt-get install -y \
  default-jre \
  wget \
  unzip \
  pigz \
  libncurses5-dev \
  zlib1g-dev \
  liblzma-dev \
  libtbb-dev \
  python3.9 \
  python3-setuptools \
  libtbb2 \
  git \
  && apt-get clean && apt-get purge
  
# install kneaddata development version for paired input processing from SRA - the only possible option for the momemnt
RUN git clone https://github.com/biobakery/kneaddata.git \
    && cd kneaddata \ 
    && python3 setup.py install --bypass-dependencies-install \ 
    && cd .. \ 
    && rm -rf kneaddata

# install trimmomatic == 0.39
RUN wget http://www.usadellab.org/cms/uploads/supplementary/Trimmomatic/Trimmomatic-$TRIMMOMATIC_V.zip \
  && unzip Trimmomatic-$TRIMMOMATIC_V.zip \
  && rm Trimmomatic-$TRIMMOMATIC_V.zip \
  && mkdir -p $APPS_HOME/Trimmomatic \
  && mv Trimmomatic-$TRIMMOMATIC_V $APPS_HOME/Trimmomatic/$TRIMMOMATIC_V \
  && printf '#!/bin/bash\njava -Xmx6g -jar ' > trimmomatic \
  && echo $APPS_HOME/Trimmomatic/$TRIMMOMATIC_V/trimmomatic-$TRIMMOMATIC_V.jar' $*' >> trimmomatic \
  && chmod +x trimmomatic \
  && mv trimmomatic /bin

# install bowtie2 == 2.4.5
RUN wget -O $APPS_DOWN/bowtie2-$BOWTIE_V.zip https://github.com/BenLangmead/bowtie2/releases/download/v$BOWTIE_V/bowtie2-$BOWTIE_V-linux-x86_64.zip \
    && cd $APPS_DOWN \
    && unzip bowtie2-$BOWTIE_V.zip \
    && cd bowtie2-$BOWTIE_V-linux-x86_64 \
    && mv bowtie2* /bin \
    && cd $APPS_DOWN \
    && rm -rf bowtie2-$BOWTIE_V-linux-x86_64

# install TRF==4.09.1
RUN wget -O trf https://github.com/Benson-Genomics-Lab/TRF/releases/download/v4.09.1/trf409.linux64 \ 
    && chmod +x trf \
    && mv trf /bin \
    && chmod 755 /app/* 

ENV PATH /app:$PATH


