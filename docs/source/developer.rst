
.. _InterSpeech proceedings paper: https://pdfs.semanticscholar.org/ddc4/5a4c828a248d34cc92275fff5ba7e23d1a32.pdf

.. _developer:

***********************
Developer documentation
***********************

This section of the documentation is devoted to explaining implementation details of PolyglotDB. In large part this is currently
a brain dump of Michael McAuliffe to hopefully allow for easier implementation of new features in the future.

The overarching structure of PolyglotDB is based around two database technologies: Neo4j and InfluxDB.  Both of these
database systems are devoted to modelling, storing, and querying specific types of data, namely, graph and time series data.
Because speech data can be modelled in each of these ways (see :ref:`dev_annotation_graphs` for more details on representing
annotations as graphs), using these databases leverages their performance and scalability for increasing PolyglotDB's ability
to deal with large speech corpora.  Please see the `InterSpeech proceedings paper`_ for more information on the high
level motivations of PolyglotDB.

Contents:

.. toctree::
   :maxdepth: 2

   developer_neo4j_implementation.rst
   developer_influxdb_implementation.rst
   io.rst
   apireference.rst