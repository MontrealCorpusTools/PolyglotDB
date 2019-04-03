
.. _LibriSpeech: http://www.openslr.org/12/

.. _Montreal Forced Aligner: https://montreal-forced-aligner.readthedocs.io/en/latest/

.. _tutorial corpus download link: https://www.dropbox.com/s/o3fdzem4soh4mtf/pg_tutorial.zip?dl=0

.. _Jupyter notebook: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_1_first_steps.ipynb

.. _full version of the script:

.. _tutorial_first_steps: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial1.py

***********************
Tutorial 1: First steps
***********************

The main objective of this tutorial is to import a downloaded corpus consisting of sound files and TextGrids into a Polyglot
database so that they can be queried.
This tutorial is available as a `Jupyter notebook`_ as well.

.. _tutorial_download:

Downloading the tutorial corpus
===============================

The tutorial corpus used here is a version of the `LibriSpeech`_ test-clean subset, forced aligned with the
`Montreal Forced Aligner`_ (`tutorial corpus download link`_).  Extract the files to somewhere on your local machine.

.. _tutorial_import:

Importing the tutorial corpus
=============================

To import the tutorial corpus, the following lines of code are necessary:

.. code-block:: python

   from polyglotdb import CorpusContext
   import polyglotdb.io as pgio

   corpus_root = '/mnt/e/Data/pg_tutorial'

   parser = pgio.inspect_mfa(corpus_root)
   parser.call_back = print

   with CorpusContext('pg_tutorial') as c:
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

   from polyglotdb import CorpusContext

   with CorpusContext('pg_tutorial') as c:
      c.reset()


.. warning::

   Be careful when running this code as it will delete any and all information in the corpus.  For smaller corpora such
   as the one presented here, the time to set up is not huge, but for larger corpora this can result in several hours worth
   of time to reimport and re-enrich the corpus.

Testing some simple queries
===========================

To ensure that data import completed successfully, we can print the list of speakers, discourses, and phone types in the corpus, via:

.. code-block:: python

   from polyglotdb import CorpusContext

   with CorpusContext('pg_tutorial') as c:
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

   with CorpusContext('pg_tutorial') as c:
      q = c.query_graph(c.phone).group_by(c.phone.label.column_name('phone'))
      results = q.aggregate(Count().column_name('count'), Average(c.phone.duration).column_name('average_duration'))
      for r in results:
         print('The phone {} had {} occurrences and an average duration of {}.'.format(r['phone'], r['count'], r['average_duration']))

Next steps
==========

You can see a `full version of the script`_.

See :ref:`tutorial_enrichment` for the next tutorial covering how to enrich the corpus and create more interesting queries.