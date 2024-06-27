
.. _LibriSpeech: http://www.openslr.org/12/

.. _Montreal Forced Aligner: https://montreal-forced-aligner.readthedocs.io/en/latest/

.. _tutorial corpus download link: https://mcgill-my.sharepoint.com/:f:/g/personal/morgan_sonderegger_mcgill_ca/EipFbcOfR31JnM4XYprp14oBuYW9lYA9IzOBcEERFZxwyA?e=tiV8bW

.. _Jupyter notebook: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_1_first_steps.ipynb

.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_1.py

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_1_subset_output.txt

.. _formant: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_formants.Rmd

.. _pitch: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_5_pitch.Rmd
 
.. _tutorial_first_steps:

***********************
Tutorial 1: First steps
***********************

The main objective of this tutorial is to import a downloaded corpus consisting of sound files and TextGrids into a Polyglot
database so that they can be queried.
This tutorial is available as a `Jupyter notebook`_ as well.

.. _tutorial_download:

Downloading the tutorial corpus
===============================

There are two corpora made available for usage with this tutorial. These are both subsets of the `LibriSpeech`_ test-clean dataset, forced aligned with the `Montreal Forced Aligner`_ 

The corpora are made available for download here: `tutorial corpus download link`_. The larger corpus, LibriSpeech-aligned, contains dozens of speakers and 490MB of data. The smaller corpus, LibriSpeech-aligned-subset, contains just two speakers from the previous corpus and therefore much less data (25MB).

In tutorials 1-3, we show how to prepare the LibriSpeech-aligned-subset corpus for linguistic analysis using polyglotdb. The subset is chosen for these tutorials to allow users to quickly test commands and compare their results with `expected results`_ while getting used to interacting with polyglotdb, since some enrichment commands can be timeconsuming when run on large datasets.

In tutorials 4 and 5, vowel `formant`_ and `pitch`_ analysis is performed and expected results are provided. These experiments are performed using the larger corpus to allow for more coherent analysis.

.. _tutorial_import:

Importing the tutorial corpus
=============================

The first step is to prepare our python environment. We begin by importing the polyglotdb libraries we need and setting useful variables:

.. code-block:: python

   from polyglotdb import CorpusContext
   import polyglotdb.io as pgio

   # This is the path to wherever you have downloaded the provided corpora directories
   corpus_root = './data/LibriSpeech-aligned-subset'
   # corpus_root = './data/LibriSpeech-aligned'

   # Corpus identifiers can be any valid string. They are unique to each corpus.
   corpus_name = 'tutorial-subset'
   # corpus_name = 'tutorial'

Then run following lines of code to import corpus data into pgdb. For any given corpora, these commands only need to be run once: corpora are preserved in pgdb after import.

.. code-block:: python

   parser = pgio.inspect_mfa(corpus_root)
   parser.call_back = print

   with CorpusContext(corpus_name) as c:
      c.load(parser, corpus_root)

.. important::

   If during the running of the import code, a ``neo4j.exceptions.ServiceUnavailable`` error is raised, then double check
   that the pgdb database is running.  Once polyglotdb is installed, simply call ``pgdb start``, assuming ``pgdb install``
   has already been called.  See :ref:`local_setup` for more information.

The import statements at the top get the necessary classes and functions for importing, namely the CorpusContext class and
the polyglot IO module.  CorpusContext objects are how all interactions with the database are handled.  The CorpusContext is
created as a context manager in Python (the ``with ... as ...`` pattern), so that clean up and closing of connections are
automatically handled both on successful completion of the code as well as if errors are encountered.

The IO module handles all import and export functionality in polyglotdb.  The principle functions that a user will encounter
are the ``inspect_X`` functions that generate parsers for corpus formats.  In the above code, the MFA parser is used because
the tutorial corpus was aligned using the MFA.  See :ref:`importing` for more information on the inspect functions and parser
objects they generate for various formats.


Resetting the corpus
--------------------

If at any point there's some error or interruption in import or other stages of the tutorial, the corpus can be reset to a
fresh state via the following code:

.. code-block:: python

   with CorpusContext(corpus_name) as c:
      c.reset()


.. warning::

   Be careful when running this code as it will delete any and all information in the corpus.  For smaller corpora such
   as the one presented here, the time to set up is not huge, but for larger corpora this can result in several hours worth
   of time to reimport and re-enrich the corpus.

Testing some simple queries
===========================

To ensure that data import completed successfully, we can print the list of speakers, discourses, and phone types in the corpus, via:

.. code-block:: python

   with CorpusContext(corpus_name) as c:
    print('Speakers:', c.speakers)
    print('Discourses:', c.discourses)

    q = c.query_lexicon(c.lexicon_phone)
    q = q.order_by(c.lexicon_phone.label)
    q = q.columns(c.lexicon_phone.label.column_name('phone'))
    results = q.all()
    print(results)

A more interesting summary query is perhaps looking at the count and average duration of different phone types across the corpus, via:

.. code-block:: python

   from polyglotdb.query.base.func import Count, Average

   with CorpusContext(corpus_name) as c:
      # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
      q = c.query_graph(c.phone).order_by(c.phone.label).group_by(c.phone.label.column_name('phone'))
      results = q.aggregate(Count().column_name('count'), Average(c.phone.duration).column_name('average_duration'))
      for r in results:
         print('The phone {} had {} occurrences and an average duration of {}.'.format(r['phone'], r['count'], r['average_duration']))

Next steps
==========

You can see a `full version of the script`_, as well as `expected output`_ when run on the 'LibriSpeech-subset' corpora.

See :ref:`tutorial_enrichment` for the next tutorial covering how to enrich the corpus and create more interesting queries.
