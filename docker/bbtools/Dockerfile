FROM ubuntu:20.04

LABEL base.image="ubuntu:20.04"
LABEL dockerfile.version="1"
LABEL software="BBTools"
LABEL software.version="38.96"
LABEL description="A set of tools labeled as \"Bestus Bioinformaticus\""
LABEL website="https://jgi.doe.gov/data-and-tools/bbtools/bb-tools-user-guide/"
LABEL license="https://jgi.doe.gov/disclaimer/"
LABEL maintainer="Chienchi Lo"
LABEL maintainer.email="chienchi@lanl.gov"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV JAVA_HOME=/usr/java/openjdk-13
ENV PATH=/usr/java/openjdk-13/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV JAVA_VERSION=13.0.1
ENV JAVA_URL=https://download.java.net/java/GA/jdk13.0.1/cec27d702aa74d5a8630c65ae61e4305/9/GPL/openjdk-13.0.1_linux-x64_bin.tar.gz
ENV JAVA_SHA256=2e01716546395694d3fad54c9b36d1cd46c5894c06f72d156772efbcf4b41335


RUN apt-get update && apt-get install -y build-essential file python \
  wget samtools curl && \
  apt-get autoclean && rm -rf /var/lib/apt/lists/*

# openjdk-13-jre \
RUN /bin/sh -c set -eux; curl -fL -o /openjdk.tgz "$JAVA_URL"; 	echo "$JAVA_SHA256 */openjdk.tgz" | sha256sum -c -; mkdir -p "$JAVA_HOME"; tar --extract --file /openjdk.tgz --directory "$JAVA_HOME" --strip-components 1; rm /openjdk.tgz; ln -sfT "$JAVA_HOME" /usr/java/default; ln -sfT "$JAVA_HOME" /usr/java/latest; for bin in "$JAVA_HOME/bin/"*; do 	base="$(basename "$bin")"; [ ! -e "/usr/bin/$base" ]; 	update-alternatives --install "/usr/bin/$base" "$base" "$bin" 20000; 	done; java -Xshare:dump; java --version; javac --version

RUN wget https://sourceforge.net/projects/bbmap/files/BBMap_38.96.tar.gz && \
  tar -xzf BBMap_38.96.tar.gz && \
  rm BBMap_38.96.tar.gz

ENV PATH="${PATH}:/bbmap"\
 LC_ALL=C

WORKDIR /data