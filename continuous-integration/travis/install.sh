#!/bin/sh
set -e
#check to see if miniconda folder is empty
if [ ! -d "$HOME/miniconda/envs/test-environment" ]; then
  wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
  chmod +x miniconda.sh
  ./miniconda.sh -b -p $HOME/miniconda
  export PATH="$HOME/miniconda/bin:$PATH"
  conda config --set always_yes yes --set changeps1 no
  conda update -q conda
  conda info -a
  conda create -q -n test-environment python=$TRAVIS_PYTHON_VERSION setuptools=18.1 atlas numpy sqlalchemy pytest
  source activate test-environment
  which python
  pip install -q coveralls coverage py2neo textgrid acousticsim
else
  echo "Miniconda already installed."
fi



