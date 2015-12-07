PolyglotDB
==========

[![Build Status](https://travis-ci.org/MontrealCorpusTools/PolyglotDB.svg?branch=master)](https://travis-ci.org/MontrealCorpusTools/PolyglotDB)
[![Coverage Status](https://coveralls.io/repos/MontrealCorpusTools/PolyglotDB/badge.svg?branch=master&service=github)](https://coveralls.io/github/MontrealCorpusTools/PolyglotDB?branch=master)
[![Documentation Status](https://readthedocs.org/projects/polyglotdb/badge/?version=latest)](http://polyglotdb.readthedocs.org/en/latest/?badge=latest)


PolyglotDB is a Python package that focuses on representing linguistic
data in relational and graph databases.

PolyglotDB represents language (speech and text corpora) using the
annotation graph formalism put forth in Bird and Liberman (2001).
Annotations are represented in a directed acyclic graph, where nodes
are points in time in an audio file or points in a text file.  Directed
edges are labelled with annotations, and mulitples levels of annotations
can be included or excluded as desired.  They put forth a relational
formalism for annotation graphs, and later work implemented the formalism in SQL.

Recently, NoSQL databases have been rising in popularity, and one type of
these is the graph database.  In this type of database, nodes and relationships
are primitives rather than relational tables.  Graph databases map on
annotation graphs in a much cleaner fashion than relational databases.
The graph database used is Neo4j (http://neo4j.com/).

Relational databases are also used in PolyglotDB.  Lexicons and segmental
inventories are represented in a relational database.  These types of
linguistic representations map well onto relational databases.

The idea of using multiple languages or technologies that suit individual
problems has been known, particularly in the realm of merging SQL and NoSQL
databases, as "polyglot persistence."

PolyglotDB was originally created for use in Phonological CorpusTools
(http://phonologicalcorpustools.github.io/CorpusTools/), developed at the
University of British Columbia.  However, primary development shifted to the
umbrella of Montreal Corpus Tools, developed by members of the Montreal
Language Modelling Lab at McGill University.

Further documentation, including installation, can be found at http://polyglotdb.readthedocs.org/en/latest/.

References
----------

`Bird, S., & Liberman, M. (2001). A formal framework for linguistic annotation. Speech communication, 33(1), 23-60.`
