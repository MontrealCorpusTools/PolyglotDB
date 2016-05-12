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
  conda create -q -n test-environment python=$TRAVIS_PYTHON_VERSION setuptools=18.1 atlas numpy sqlalchemy pytest scipy scikit-learn networkx
  source activate test-environment
  which python
  pip install -q coveralls coverage py2neo textgrid acousticsim
else
  echo "Miniconda already installed."
fi

if [ ! -d "$HOME/neo4j/neo4j" ]; then
  mkdir -p $HOME/neo4j
  wget http://dist.neo4j.org/neo4j-community-2.3.3-unix.tar.gz
  tar -xzf neo4j-community-2.3.3-unix.tar.gz -C $HOME/neo4j
  mv $HOME/neo4j/neo4j-community-2.3.3 $HOME/neo4j/neo4j
  sed -i.bak s/#dbms.security.auth_enabled=false/dbms.security.auth_enabled=false/g $HOME/neo4j/neo4j/conf/neo4j.conf
  sed -i.bak s/dbms.directories.import=import/#dbms.directories.import=import/g $HOME/neo4j/neo4j/conf/neo4j.conf
else
  echo "Neo4j already installed."
fi
