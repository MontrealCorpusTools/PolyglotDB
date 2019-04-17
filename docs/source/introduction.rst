.. _introduction:

************
Introduction
************


.. _Phonological CorpusTools: http://phonologicalcorpustools.github.io/CorpusTools/

.. _GitHub repository: https://github.com/PhonologicalCorpusTools/PolyglotDB/

.. _Neo4j: http://neo4j.com/

.. _InfluxDB: http://influxdb.com/

.. _michael.e.mcauliffe@gmail.com: michael.e.mcauliffe@gmail.com

.. _EMU-SDMS: https://ips-lmu.github.io/EMU.html

.. _LaBB-CAT: http://labbcat.sourceforge.net/

.. _general_background:

.. _[PDF]: https://pdfs.semanticscholar.org/ddc4/5a4c828a248d34cc92275fff5ba7e23d1a32.pdf

.. _@mmcauliffe: https://github.com/mmcauliffe

.. _@esteng: https://github.com/esteng

.. _@samihuc: https://github.com/samihuc

.. _@MichaelGoodale: https://github.com/MichaelGoodale

.. _@jeffmielke: https://github.com/jeffmielke

.. _@a-coles: https://github.com/a-coles

.. _ISCAN documentation: https://iscan.readthedocs.io/en/latest/

.. _Speech Corpus Tools: https://github.com/MontrealCorpusTools/speechcorpustools

.. _Montreal Corpus Tools: https://github.com/MontrealCorpusTools

.. _Montreal Language Modelling Lab: https://github.com/mlml/

.. _SPADE GitHub repo: https://github.com/MontrealCorpusTools/SPADE

.. _ISCAN conference paper: https://spade.glasgow.ac.uk/wp-content/uploads/2019/04/iscan-icphs2019-revised.pdf

.. _SPADE project: https://spade.glasgow.ac.uk

.. _MCQLL lab: http://mcqll.org/



.. _InterSpeech proceedings paper: https://pdfs.semanticscholar.org/ddc4/5a4c828a248d34cc92275fff5ba7e23d1a32.pdf

General Background
==================

**PolyglotDB** is a Python package that focuses on representing linguistic
data in scalable, high-performance databases (called "Polyglot"
databases here) to apply acoustic
analysis and other algorithms to large speech corpora.  

In general there are two ways to leverage PolyglotDB for analyzing a
dataset:

1. The first way, more appropriate for technically skilled users, is
   through a Python API: writing Python scripts that import functions
   and classes from PolyglotDB.  (For this route, see
   :ref:`installation` for setting up PolyglotDB, followed by
   :ref:`tutorial` for walk-through examples.)  This way also makes
   more sense for users in an individual lab, where it can be assumed
   that all users have the same level of access to datasets (without
   any ethical issues).

2.  The second way, more appropriate for a user group dispersed across
    multiple sites and where some users are less comfortable with
    Python scripting, is by setting up an ISCAN (Integrated Speech
    Corpus ANalysis) server---see the `ISCAN documentation`_ for more
    details.  ISCAN servers allow users to view information and
    perform most functions of PolyglotDB through a web browser.  In
    addition, ISCAN servers include features for the use case of
    multiple datasets with differential access: by user/corpus
    permissions level, and functionality for managing multiple
    Polyglot databases.  

This documentation site is relevant for ways PolyglotDB canbeused, but
is geared towards a technically-skilled user and thus focuses more on
the use case of using PolyglotDB "by script" (#1).
    
The general workflow for working with PolyglotDB is:

* **Import**

  - Parse and load initial data from corpus files into a Polyglot
    database

    * This step can take a while, from a couple of minutes to hours depending on corpus size.

    * Intended to be done once per corpus
      
  - See :ref:`tutorial_import` for an example
    
  - See :ref:`importing` for more details on the import process

* **Enrichment**

  - Add further information through analysis algorithms or from CSV files

    * Can take a while, from a couple of minutes to hours depending on
      enrichment and corpus size

    * Intended to be done once per corpus

  - See :ref:`tutorial_enrichment` for an example

  - See :ref:`enrichment` for more details on the enrichment process

* **Query**
  
  - Find specific linguistic units
    
    * Should be quick, from a couple of minutes to ~10 minutes
      depending on corpus size
      
    * Intended to be done many times per corpus, for different queries
    
  - See :ref:`tutorial_query` for an example
  
  - See :ref:`queries` for more details on the query process

  
* **Export**

  - Generate a CSV file for data analysis with specific information extracted from the previous query

    * Should be quick, and intended to be done many times per corpus
      (like Query)

  - See :ref:`tutorial_export` for an example
  
  - See :ref:`export` for more details on the export process


The thinking behind this workflow is explained in more detail in the
`ISCAN conference paper`_.
    
.. note::

   There are also many PolyglotDB scripts written for the `SPADE project`_ that can be used as examples.  These scripts are
   available in the `SPADE GitHub repo`_.

High level overview
-------------------

PolyglotDB represents language (speech and text corpora) using the
annotation graph formalism put forth in Bird and Liberman (2001).
Annotations are represented in a directed acyclic graph, where nodes
are points in time in an audio file or points in a text file.  Directed
edges are labelled with annotations, and multiple levels of annotations
can be included or excluded as desired.  They put forth a relational
formalism for annotation graphs, and later work implements the formalism in SQL.  Similarly, the `LaBB-CAT`_ and `EMU-SDMS`_
use the annotation graph formalism.

Recently, NoSQL databases have been rising in popularity, and one type of
these is the graph database.  In this type of database, nodes and relationships
are primitives rather than relational tables.  Graph databases map on
annotation graphs in a much cleaner fashion than relational databases.
The graph database used in PolyglotDB is `Neo4j`_.

PolyglotDB also uses a NoSQL time-series database called `InfluxDB`_.
Acoustic measurements like F0 and formants are stored here as every time step (10 ms)
has a value associated with it.  Each measurement is also associated with a speaker and a phone from
the graph database.

Multiple versions of imported sound files are generated at
various sampling rates (1200 Hz, 11000 Hz, and 22050 Hz) to help speed up relevant algorithms.  For example, pitch algorithms don't need a
highly sampled signal and higher sample rates will slow down the processing of files.

The idea of using multiple languages or technologies that suit individual
problems has been known, particularly in the realm of merging SQL and NoSQL
databases, as "polyglot persistence."

More detailed information on specific implementation details is available in the :ref:`developer`, as well as in the
`InterSpeech proceedings paper`_.

Development history
===================

PolyglotDB was originally conceptualized for use in `Phonological CorpusTools`_, developed at the
University of British Columbia.  However, primary development shifted to the
umbrella of `Montreal Corpus Tools`_, developed by members of the `Montreal
Language Modelling Lab`_ at McGill University (now part of `MCQLL Lab`_).

A graphical program named `Speech Corpus Tools`_ was originally
developed to allow users to interact with Polyglot without writing
scripts.  However, in the context of the the Speech Across Dialects of
English (SPADE) project, a more flexible solution was needed to
accommodate use cases involving multiple users, with physical
separation between users and data, and differing levels of permission
across datasets.  ISCAN has been developed within the SPADE project
with these requirements in mind.

Contributors
------------

* Michael McAuliffe (`@mmcauliffe`_)
* Elias Stengel-Eskin (`@esteng`_)
* Sarah Mihuc (`@samihuc`_)
* Michael Goodale (`@MichaelGoodale`_)
* Jeff Mielke (`@jeffmielke`_)
* Arlie Coles (`@a-coles`_)


Citation
--------

A citeable paper for PolyglotDB is:

McAuliffe, Michael, Elias Stengel-Eskin, Michaela Socolof, and Morgan Sonderegger (2017). Polyglot and Speech Corpus Tools:
a system for representing, integrating, and querying speech corpora. In Proceedings of Interspeech 2017. `[PDF]`_

Or you can cite it via:

McAuliffe, Michael, Elias Stengel-Eskin, Michaela Socolof, Arlie Coles, Sarah Mihuc, Michael Goodale, and Morgan Sonderegger (2019).
PolyglotDB [Computer program]. Version 0.1.0, retrieved 26 March 2019 from https://github.com/MontrealCorpusTools/PolyglotDB.

