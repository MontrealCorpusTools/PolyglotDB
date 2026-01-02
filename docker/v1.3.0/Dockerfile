# Use an official Python 3.12 image from the Python repository
FROM --platform=linux/amd64 python:3.12-slim

ENV PGDB_HOME=/pgdb

WORKDIR /polyglotdb

RUN mkdir -p /pgdb

RUN apt update && apt install -y \
    wget \
    build-essential \
    libpq-dev \
    tar \
    libsndfile1 \
    git \
    cmake \
    nano \
    vim

# Install praat
RUN wget https://www.fon.hum.uva.nl/praat/praat6417_linux-intel64-barren.tar.gz \
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

# Copy the config file
COPY ./config.ini /pgdb/config.ini

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install polyglotdb

# Set up the entry point for the container
ENTRYPOINT ["/bin/bash"]
