.. _introduction:

************
Introduction
************


.. _PGDB website: http://phonologicalcorpustools.github.io/PolyglotDB/

.. _Phonological CorpusTools: http://phonologicalcorpustools.github.io/CorpusTools/

.. _GitHub repository: https://github.com/PhonologicalCorpusTools/PolyglotDB/

.. _Neo4j: http://neo4j.com/

.. _InfluxDB: http://influxdb.com/

.. _michael.e.mcauliffe@gmail.com: michael.e.mcauliffe@gmail.com

.. _EMU-SDMS: https://ips-lmu.github.io/EMU.html

.. _LaBB-CAT: http://labbcat.sourceforge.net/

.. _general_background:

General Background
==================

*PolyglotDB* is a Python package that focuses on representing linguistic
data in relational and graph databases.

PolyglotDB represents language (speech and text corpora) using the
annotation graph formalism put forth in Bird and Liberman (2001).
Annotations are represented in a directed acyclic graph, where nodes
are points in time in an audio file or points in a text file.  Directed
edges are labelled with annotations, and multiple levels of annotations
can be included or excluded as desired.  They put forth a relational
formalism for annotation graphs, and later work implements the formalism in SQL.  Similarly, the `LaBB-CAT`_ and `EMU-SDMS`_
use the annotation graph formalism

Recently, NoSQL databases have been rising in popularity, and one type of
these is the graph database.  In this type of database, nodes and relationships
are primitives rather than relational tables.  Graph databases map on
annotation graphs in a much cleaner fashion than relational databases.
The graph database used in PolyglotDB is `Neo4j`_.

PolyglotDB also uses a NoSQL timeseries database called `InfluxDB`_.
Acoustic measurements like F0 and formants are stored here as every time step (10 ms)
has a value associated with it.  Each measurement is also associated with a speaker and a phone from
the graph database.

Relational databases are also used in PolyglotDB.  The relational database is mainly used to track metadata about the
corpus, particularly the sound files that are generated during import. Multiple versions of imported sound files are generated at
various sampling rates (1200 Hz, 11000 Hz, and 22050 Hz) to help speed up relevant algorithms.  For example, pitch algorithms don't need a
highly sampled signal and higher sample rates will slow down the processing of files.

The idea of using multiple languages or technologies that suit individual
problems has been known, particularly in the realm of merging SQL and NoSQL
databases, as "polyglot persistence."

PolyglotDB was originally conceptualized for use in `Phonological CorpusTools`_, developed at the
University of British Columbia.  However, primary development shifted to the
umbrella of Montreal Corpus Tools, developed by members of the Montreal
Language Modelling Lab at McGill University.