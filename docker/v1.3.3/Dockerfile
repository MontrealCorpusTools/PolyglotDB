FROM continuumio/miniconda3

ENV PGDB_HOME=/pgdb

WORKDIR /polyglotdb

RUN mkdir -p /pgdb

RUN apt update && apt install -y \
    wget \
    build-essential \
    libpq-dev \
    tar \
    git \
    cmake \
    nano \
    vim

# Install praat
RUN wget https://www.fon.hum.uva.nl/praat/praat6439_linux-intel64-barren.tar.gz \
&& tar -xvzf praat6417_linux-intel64-barren.tar.gz \
&& mkdir /pgdb/tools \
&& mv praat_barren /pgdb/tools/praat \
&& rm praat6417_linux-intel64-barren.tar.gz

ENV praat=/pgdb/tools/praat

# Install reaper
RUN git clone https://github.com/google/REAPER.git \
&& cd REAPER \
&& mkdir build \
&& cd build \
&& cmake .. \
&& make \
&& mv reaper /pgdb/tools/reaper \
&& cd ../.. \
&& rm -r REAPER

ENV reaper=/pgdb/tools/reaper

COPY ./config.ini /pgdb/config.ini

# Create a new conda environment named polyglotdb with Python 3.12
RUN conda create -n polyglotdb -c conda-forge polyglotdb python=3.12

# Make sure bash is the default shell
SHELL ["/bin/bash", "-c"]

# Set entrypoint to activate the environment and launch an interactive shell
ENTRYPOINT ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate polyglotdb && exec bash"]
