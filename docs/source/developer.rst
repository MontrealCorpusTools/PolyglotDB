.. _InterSpeech proceedings paper: https://pdfs.semanticscholar.org/ddc4/5a4c828a248d34cc92275fff5ba7e23d1a32.pdf

.. _EMU-SDMS: https://ips-lmu.github.io/EMU.html

.. _LaBB-CAT: http://labbcat.sourceforge.net/

.. _ISCAN conference paper: https://spade.glasgow.ac.uk/wp-content/uploads/2019/04/iscan-icphs2019-revised.pdf

.. _ISCAN documentation: https://iscan.readthedocs.io/en/latest/

.. _Neo4j: http://neo4j.com/

.. _InfluxDB: http://influxdb.com/


.. _developer:

***********************
Developer documentation
***********************

This section of the documentation explains implementation details of PolyglotDB.

.. In large part this is currently a brain dump of Michael McAuliffe to hopefully allow for easier implementation of new features in the future.

Overview
--------

PolyglotDB represents language (speech and text corpora) using the
annotation graph formalism put forth by :cite:t:`bird2001formal`.
Annotations are represented in a directed acyclic graph, where nodes
are points in time in an audio file or points in a text file.  Directed
edges are labelled with annotations, and multiple levels of annotations
can be included or excluded as desired.  They put forth a relational
formalism for annotation graphs, and later work implements the formalism in SQL. Similarly, the `LaBB-CAT`_ and `EMU-SDMS`_
speech database management systems
use the annotation graph formalism, but implemented in SQL databases.

PolyglotDB uses a different approach to the annotation graph formalism, using *NoSQL* databases. One
type of NoSQL database is the graph database, where nodes and relationships
are primitives rather than relational tables. Graph databases map onto
annotation graphs in a much cleaner fashion than relational databases, allowing the database to closely match the structure of
speech corpora.
The graph database used in PolyglotDB is `Neo4j`_.

PolyglotDB also uses a NoSQL time-series database called `InfluxDB`_.
Acoustic measurements like F0 and formants are stored here as every time step (10 ms)
has a value associated with it. Each measurement is also associated with a speaker and a phone from
the graph database.

Multiple versions of imported sound files are generated at
various sampling rates (1200 Hz, 11000 Hz, and 22050 Hz) to help speed up relevant algorithms. For example, pitch algorithms don't need a
highly sampled signal and higher sample rates will slow down the processing of files.

The overarching structure of PolyglotDB is based around these two database technologies: Neo4j and InfluxDB. (A SQL database is also used
for certain tasks.) Both of these
database systems are devoted to modelling, storing, and querying specific types of data, namely, graph and time series data.
Because speech data can be modelled in each of these ways (see :ref:`dev_annotation_graphs` for more details on representing
annotations as graphs), using these databases leverages their performance and scalability for increasing PolyglotDB's ability
to deal with large speech corpora.

The idea of using multiple languages or technologies that suit individual
problems has been known, particularly in the realm of merging SQL and NoSQL
databases, as "polyglot persistence", hence the name PolyglotDB.

Please see the `InterSpeech proceedings paper`_ for more information on the high-level motivations for PolyglotDB.

.. note::
   `ISCAN <https://github.com/MontrealCorpusTools/ISCAN/>`_ is a separate project built on top of PolyglotDB that provides a web-based interface for corpus management and analysis.
   An Integrated Speech Corpus Analysis (ISCAN) server can be set up on a lab's central server, or you can run it on your
   local computer as well (though many
   of PolyglotDB's algorithms benefit from having more processors and memory available). Please see the `ISCAN
   documentation`_ for more information on setting it up and the `ISCAN conference paper`_ for details.
   The main feature benefits of ISCAN are multiple Polyglot databases (separating out different corpora and allowing any
   of them to be started or shutdown), graphical interfaces for inspecting data, and a user authentication system with different levels
   of permission for remote access through a web application. ISCAN is not actively maintained as of 2025 and may require additional effort
   to configure and use. It is not the recommended or default option for most users. The primary and
   supported way to interact with PolyglotDB remains through its Python API.


Contents
--------

.. toctree::
   :maxdepth: 2

   developer_neo4j_implementation.rst
   developer_influxdb_implementation.rst
   io.rst
   apireference.rst
