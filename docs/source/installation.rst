.. _installation:

************
Installation
************

.. _prerequisites:

Prerequisites
=============

PolyglotDB uses Neo4j to represent its annotation graphs.  Before installing
PolyglotDB, download and install the Neo4j Community edition
(http://neo4j.com/download/).

Once Neo4j is installed, start the server and go to http://localhost:7474/.
The first time, Neo4j will prompt you to set a password for future connections.

PolyglotDB currently only supports SQLite for its relational database component,
which requires no extra installation.
In the future, more sophisticated relational database servers will be supported.

.. _actual_install:

Installation
============

Once Neo4j is installed and running, clone or download the Git repository
(https://github.com/PhonologicalCorpusTools/PolyglotDB).  Navigate to
the diretory via command line and install via :code:`python setup.py install`.

