#!/bin/sh
set -e
mkdir $HOME/downloads
#check to see if miniconda folder is empty
if [ ! -d "$HOME/miniconda/miniconda/envs/test-environment" ]; then
  wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
  chmod +x miniconda.sh
  ./miniconda.sh -b -p $HOME/miniconda/miniconda
  export PATH="$HOME/miniconda/miniconda/bin:$PATH"
  conda config --set always_yes yes --set changeps1 no
  conda update -q conda
  conda info -a
  conda create -q -n test-environment python=$TRAVIS_PYTHON_VERSION setuptools atlas numpy pytest scipy
  source activate test-environment
  which python
  pip install -q coveralls coverage neo4j-driver textgrid librosa tqdm influxdb conch_sounds
  python setup.py install
else
  echo "Miniconda already installed."
fi

if [ ! -d "$HOME/miniconda/miniconda/envs/test-server-environment" ]; then
  export PATH="$HOME/miniconda/miniconda/bin:$PATH"
  conda create -q -n test-server-environment python=$TRAVIS_PYTHON_VERSION setuptools atlas numpy pytest scipy
  source activate test-server-environment
  which python
  pip install -q coveralls coverage neo4j-driver textgrid librosa tqdm influxdb django conch_sounds
  python setup.py install
else
  export PATH="$HOME/miniconda/miniconda/bin:$PATH"
  source activate test-server-environment
  python setup.py install
  echo "Server already installed."
fi

if [ ! -d "$HOME/pgdb/data" ]; then
  source activate test-environment
  pgdb install ~/pgdb -q
else
  echo "Neo4j and InfluxDB already installed."
fi


if [ ! -f "$HOME/tools/praat" ]; then
  cd $HOME/downloads
  #FOR WHEN TRAVIS UPDATES TO A NEWER UBUNTU
  latestVer=$(curl -s 'http://www.fon.hum.uva.nl/praat/download_linux.html' |
   grep -Eo 'praat[0-9]+_linux64barren\.tar\.gz' | head -1)

  # Download.
  curl "http://www.fon.hum.uva.nl/praat/${latestVer}" > praat-latest.tar.gz
  tar -zxvf praat-latest.tar.gz
  mv praat_barren $HOME/tools/praat
else
  echo "Praat already installed."
fi

if [ ! -f "$HOME/tools/reaper" ]; then
  cd $HOME/downloads
  git clone https://github.com/google/REAPER.git
  cd REAPER
  mkdir build
  cd build
  cmake ..
  make
  mv reaper $HOME/tools/reaper
else
  echo "Reaper already installed"
fi