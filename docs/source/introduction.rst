.. _introduction:

************
Introduction
************

.. _Phonological CorpusTools: http://phonologicalcorpustools.github.io/CorpusTools/

.. _GitHub repository: https://github.com/PhonologicalCorpusTools/PolyglotDB/


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

.. _ISCAN GitHub repository: https://github.com/MontrealCorpusTools/ISCAN/tree/main

.. _Speech Corpus Tools: https://github.com/MontrealCorpusTools/speechcorpustools

.. _Montreal Corpus Tools: https://github.com/MontrealCorpusTools

.. _Montreal Language Modelling Lab: https://github.com/mlml/

.. _SPADE GitHub repo: https://github.com/MontrealCorpusTools/SPADE

.. _ISCAN conference paper: https://spade.glasgow.ac.uk/wp-content/uploads/2019/04/iscan-icphs2019-revised.pdf

.. _PolyglotDB conference paper: https://www.isca-archive.org/interspeech_2017/mcauliffe17b_interspeech.pdf

.. _SPADE project: https://spade.glasgow.ac.uk

.. _MCQLL lab: http://mcqll.org/

Background
==========

**PolyglotDB** is a Python package for storage, phonetic analysis, and querying of speech corpora. It
represents linguistic data in scalable, high-performance databases (called "Polyglot"
databases here) to apply acoustic analysis and other algorithms to speech corpora.  While PolyglotDB can be
used with corpora of any size, it is built to scale to very large corpora.  It is most often used on corpora aligned
with the `Montreal Forced Aligner <https://montreal-forced-aligner.readthedocs.io/en/latest/>`_, but accepts corpora in other formats as well.

Users interact with PolyglotDB primarily through its Python API: writing Python scripts
that import functions and classes from PolyglotDB. See :ref:`installation` for setting up PolyglotDB,
followed by :ref:`tutorials` for walk-through examples.  :ref:`case_studies` show concrete cases of PolyglotDB's use to address different kinds of phonetic research
questions.


The general workflow for working with PolyglotDB is:

* **Import**

  - Parse and load initial data from corpus files into a Polyglot
    database.

  - See :ref:`tutorial_first_steps` for an example, using a tutorial corpus.

  - See :ref:`importing` for more details on the import process.

* **Enrichment**

  - Add further information through analysis algorithms or from CSV files.

  - See :ref:`tutorial_enrichment` for an example.

  - See :ref:`enrichment` for more details on the enrichment process.

* **Query**

  - Find specific linguistic units.

  - See :ref:`tutorial_query` for an example.

  - See :ref:`queries` for more details on the query process.


* **Export**

  - Generate a CSV file for data analysis with specific information extracted from the previous query.

  - See :ref:`tutorial_export` for an example.

  - See :ref:`export` for more details on the export process.


More detailed information on specific implementation details is available in the :ref:`developer`,
as well as in the `PolyglotDB conference paper`_ and the `ISCAN conference paper`_.


Applications
============

In addition to tutorials, there are worked examples of PolyglotDB's use to answer real-world research questions,
in :ref:`case_studies`. These are Python scripts along with explanations of the entire workflow.

Further examples of PolyglotDB scripts used in the `SPADE project`_ are available in the `SPADE GitHub repo`_ (but without accompanying explanations). Both contain scripts which can be used as examples to work from for your own studies.

Some studies which have used PolyglotDB are:

* Sibilant moments: :cite:t:`stuart2019large`, :cite:t:`gunter2021contextualizing`, :cite:t:`sonderegger2023how`

* Segment durations: :cite:t:`tanner2020toward`, :cite:t:`lo2023articulation`

* Vowel formants: :cite:t:`mielke2019age`, :cite:t:`tanner2022multidimensional`, :cite:t:`lipari2025new`

* f0: :cite:t:`ting2025crosslinguistic`

* Finding tokens: :cite:t:`johnson2024language`

.. note::

  For those interested in a web-based interface, `ISCAN <https://github.com/MontrealCorpusTools/ISCAN/>`_ (Integrated Speech Corpus ANalysis) is a separate
  project built on top of PolyglotDB. ISCAN is not actively maintained as of 2025. See :ref:`developer` for more information.
.. ISCAN servers allow users to view information and perform
.. most functions of PolyglotDB through a web browser.
.. See the `ISCAN documentation`_ for more details on setting it up.
.. Note, however, that ISCAN is not actively maintained as of 2025 and may require additional effort
.. to configure and use. It is not the recommended or default option for most users. The primary and
.. supported way to interact with PolyglotDB remains through its Python API.


Contributors
============

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
========

If you use PolyglotDB in your research, please cite the following paper:

McAuliffe, Michael, Elias Stengel-Eskin, Michaela Socolof, and Morgan Sonderegger (2017). Polyglot and Speech Corpus Tools:
a system for representing, integrating, and querying speech corpora. In *Proceedings of Interspeech 2017*, pp. 3887–3891. https://doi.org/10.21437/Interspeech.2017-1390.
