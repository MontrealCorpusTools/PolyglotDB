#!/bin/sh
set -e
#check to see if miniconda folder is empty
if [ ! -d "$HOME/miniconda/miniconda/envs/test-environment" ]; then
  wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
  chmod +x miniconda.sh
  ./miniconda.sh -b -p $HOME/miniconda/miniconda
  export PATH="$HOME/miniconda/miniconda/bin:$PATH"
  conda config --set always_yes yes --set changeps1 no
  conda update -q conda
  conda info -a
  conda create -q -n test-environment python=3.5 setuptools atlas numpy sqlalchemy pytest scipy scikit-learn networkx
  source activate test-environment
  which python
  pip install -q coveralls coverage py2neo textgrid acousticsim librosa tqdm influxdb
else
  echo "Miniconda already installed."
fi

if [ ! -d "$HOME/pgdb/data" ]; then
  source activate test-environment
  python bin/pgdb.py install ~/pgdb
else
  echo "Neo4j and InfluxDB already installed."
fi
