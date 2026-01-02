
.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_1.py

.. _formant: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_formants.Rmd

.. _pitch: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_5_pitch.Rmd

.. _tutorial scripts: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial

.. _Steps to use PolyglotDB: https://polyglotdb.readthedocs.io/en/latest/getting_started.html#steps-to-use-polyglotdb

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/blob/main/examples/tutorial/results/tutorial_1_subset_output.txt

.. _tutorial_first_steps:

***********************
Tutorial 1: First steps
***********************


Preliminaries
=============

Before starting, make sure you have:

* Activated your PolyglotDB conda environment with ``conda activate polyglotdb``.
* Started the local PolyglotDB database with ``pgdb start``.
* Downloaded the tutorial corpus (see :ref:`here<tutorial_download>`).

See `Steps to use PolyglotDB`_ for detailed instructions.

The objective of this tutorial is to import a downloaded corpus consisting of sound files and TextGrids into a Polyglot
database, which will then be enriched and queried (in Tutorials 2-3).

.. _tutorial_1_workflow:

Workflow
--------

After the preliminary steps above, this tutorial can be followed in two ways:

1. **Step-by-step** - start the python interpreter with ``python`` and then copy and paste each code block one at a time.
2. **Script mode** -  run the entire script directly as a standalone Python file.

To run the full tutorial script from the command line:

.. code-block:: bash

   python tutorial_1.py

Before running this, make sure to edit the `corpus_root` variable in `tutorial_1.py` to point to the correct path where you downloaded the tutorial corpus.
The full script is available here: `tutorial scripts`_.

.. _tutorial_import:

Importing the tutorial corpus
=============================

The first step is to prepare our Python environment. We begin by importing the PolyglotDB libraries we need and setting useful variables:

.. code-block:: python

   from polyglotdb import CorpusContext
   import polyglotdb.io as pgio

   # This is the path to wherever you have downloaded the provided corpora directories
   corpus_root = './data/LibriSpeech-aligned-subset'
   # corpus_root = './data/LibriSpeech-aligned'

   # Corpus identifiers can be any valid string. They are unique to each corpus.
   corpus_name = 'tutorial-subset'
   # corpus_name = 'tutorial'

Then run following lines of code to import corpus data into the PolyglotDB database. For any given corpus, these commands only need to be run once: corpora are preserved in the database after import.

.. code-block:: python

   parser = pgio.inspect_mfa(corpus_root)
   parser.call_back = print

   with CorpusContext(corpus_name) as c:
      c.load(parser, corpus_root)

The ``pgio`` module handles all import and export functionality in PolyglotDB.  The principle functions that a user will encounter
are the ``inspect_X`` functions that generate parsers for corpus formats.  In the above code, the MFA parser is used because
the tutorial corpus was aligned using the MFA.  See :ref:`importing` for more information on the inspect functions and parser
objects they generate for various formats.

.. warning::

   If during the running of the import code, a ``neo4j.exceptions.ServiceUnavailable`` error is raised, then double check
   that the  database is running.  Once PolyglotDB is installed, simply call ``pgdb start``, assuming ``pgdb install``
   has already been called. See :ref:`local_setup` for more information.


.. admonition:: Technical detail

   The import statements at the top get the necessary classes and functions for importing, namely the ``CorpusContext`` class and
   the ``pgio`` ("PolyglotDB input-output") module.  ``CorpusContext`` objects are how all interactions with the database are handled. The ``CorpusContext`` is
   created as a context manager in Python (the ``with ... as ...`` pattern), so that clean up and closing of connections are
   automatically handled both on successful completion of the code as well as if errors are encountered.


.. _resetting:

Resetting the corpus
--------------------

If at any point there's some error or interruption in import or other stages of the tutorial, the corpus can be reset to a
fresh state via the following code:

.. code-block:: python

   with CorpusContext(corpus_name) as c:
      c.reset()


.. warning::

   Be careful when running this code as it will delete any and all information in the corpus.  For smaller corpora such
   as the one presented here, set up time is not huge, but for larger corpora this can result in several hours worth
   of time to re-import and re-enrich the corpus.


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
