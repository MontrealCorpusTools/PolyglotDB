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

.. _@lxy2304: https://github.com/lxy2304

.. _@massimolipari: https://github.com/massimolipari

.. _@michaelhaaf: https://github.com/michaelhaaf

.. _@james-tanner: https://github.com/james-tanner

.. _@msonderegger: https://github.com/msonderegger

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

.. _PolyglotDB conference paper: https://www.isca-archive.org/interspeech_2017/mcauliffe17b_interspeech.pdf

.. _SPADE project: https://spade.glasgow.ac.uk

.. _MCQLL lab: http://mcqll.org/


General Background
==================

**PolyglotDB** is a Python package for storage, phonetic analysis, and querying of speech corpora. It
represents linguistic data in scalable, high-performance databases (called "Polyglot"
databases here) to apply acoustic analysis and other algorithms to speech corpora.  While PolyglotDB can be
used with corpora of any size, it is built to scale to very large corpora.

Users interact with PolyglotDB primarily through its Python API: writing Python scripts 
that import functions and classes from PolyglotDB. See :ref:`installation` for setting up PolyglotDB
, followed by :ref:`tutorial` for walk-through examples.  :ref:`case_studies` show concrete cases of PolyglotDB's use to address different kinds of phonetic research questions.


The general workflow for working with PolyglotDB is:

* **Import**

  - Parse and load initial data from corpus files into a Polyglot
    database
      
  - See :ref:`tutorial_import` for an example
    
  - See :ref:`importing` for more details on the import process

* **Enrichment**

  - Add further information through analysis algorithms or from CSV files

  - See :ref:`tutorial_enrichment` for an example

  - See :ref:`enrichment` for more details on the enrichment process

* **Query**
  
  - Find specific linguistic units
    
  - See :ref:`tutorial_query` for an example
  
  - See :ref:`queries` for more details on the query process

  
* **Export**

  - Generate a CSV file for data analysis with specific information extracted from the previous query

  - See :ref:`tutorial_export` for an example
  
  - See :ref:`export` for more details on the export process


The thinking behind this workflow is explained in more detail in the `PolyglotDB conference paper`_ and the
`ISCAN conference paper`_.
    
.. note::
   Worked examples of PolyglotDB's use are in :ref:`case_studies`. Further examples of PolyglotDB scripts used in the `SPADE project`_ are
   available in the `SPADE GitHub repo`_.  Both contain scripts which can be used as examples to work from for your own studies.

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

More detailed information on specific implementation details is available in the :ref:`developer`, as well as in the `PolyglotDB conference paper`_ and the `ISCAN conference paper`_.


.. note::

  For those interested in a web-based interface, ISCAN (Integrated Speech Corpus ANalysis) is a separate 
  project built on top of PolyglotDB. ISCAN servers allow users to view information and perform 
  most functions of PolyglotDB through a web browser. 
  See the `ISCAN documentation`_ for more details on setting it up.
  Note, however, that ISCAN is not actively maintained as of 2025 and may require additional effort 
  to configure and use. It is not the recommended or default option for most users. The primary and 
  supported way to interact with PolyglotDB remains through its Python API.


Contributors
------------

* Michael McAuliffe (`@mmcauliffe`_)
* Xiaoyi Li (`@lxy2304`_)
* Michael Haaf (`@michaelhaaf`_)
* Elias Stengel-Eskin (`@esteng`_)
* Arlie Coles (`@a-coles`_)
* Sarah Mihuc (`@samihuc`_)
* Michael Goodale (`@MichaelGoodale`_)
* Massimo Lipari  (`@massimolipari`_)
* Jeff Mielke (`@jeffmielke`_)
* James Tanner (`@james-tanner`_)
* Morgan Sonderegger (`@msonderegger`_)


Citation
--------

A citeable paper for PolyglotDB is:

McAuliffe, Michael, Elias Stengel-Eskin, Michaela Socolof, and Morgan Sonderegger (2017). Polyglot and Speech Corpus Tools:
a system for representing, integrating, and querying speech corpora. In *Proceedings of Interspeech 2017*, pp. 3887–3891. https://doi.org/10.21437/Interspeech.2017-1390.
