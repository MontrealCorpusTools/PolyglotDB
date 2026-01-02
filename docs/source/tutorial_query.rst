
.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_3.py

.. _related ISCAN tutorial: https://iscan.readthedocs.io/en/latest/tutorials_iscan.html#examining-analysing-the-data

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_3_subset_output.csv

.. _tutorial scripts: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial

.. _tutorial_query:

***********************************
Tutorial 3: Getting information out
***********************************


Preliminaries
=============

The objective of this tutorial is to export a CSV file using a query on an imported (:ref:`tutorial_first_steps`) and
enriched (:ref:`tutorial_enrichment`) corpus.

The complete Python script for Tutorial 3 is available here: `tutorial scripts`_.

Workflow
========


This tutorial assumes you have already done Tutorials 1 and 2. Tutorial 3 can be followed in two ways, like Tutorials 1-2 (see :ref:`here<tutorial_1_workflow>`):

* Pasting in commands one by one into the Python interpreter
* Running the entire script at once (``python tutorial_3.py``)

Running the whole script is the usual workflow for PolyglotDB, but the commands are shown one by one here to make it easier to follow along.


As in Tutorials 1-2, ``import`` statements and the location of the corpus (``corpus_root``) must be set for the code in this tutorial
to be runnable:

.. code-block:: python

    from polyglotdb import CorpusContext

    corpus_name = 'tutorial-subset'
    export_path = './results/tutorial_3_subset_output.csv'
    # change export_path to the location where you want the CSV file to be saved


Creating an initial query
=========================

The first steps for generating a CSV file is to create a query that
selects just the linguistic objects ("annotations") of a particular
type (e.g. words, syllables) that are of interest to our study.

For this example, we will query for all *syllables*, which are:

  - `stressed` (defined here as having a ``stress`` value equal to
    ``'1'``)
  - At the beginning of the word,
  - In words that are at the end of utterances.

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.stress == '1') # Stressed syllables...
        q = q.filter(c.syllable.begin == c.syllable.word.begin) # That are at the beginning of words...
        q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end) # that are at the end of utterances.


Next, we want to specify the particular information to extract for each syllable found.

.. code-block:: python

    # duplicated from above
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.stress == '1') # Stressed syllables...
        q = q.filter(c.syllable.begin == c.syllable.word.begin) # That are at the beginning of words...
        q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end) # that are at the end of utterances.

        q = q.columns(c.syllable.label.column_name('syllable'),
                      c.syllable.duration.column_name('syllable_duration'),
                      c.syllable.word.label.column_name('word'),
                      c.syllable.word.begin.column_name('word_begin'),
                      c.syllable.word.end.column_name('word_end'),
                      c.syllable.word.num_syllables.column_name('word_num_syllables'),
                      c.syllable.word.stress_pattern.column_name('word_stress_pattern'),
                      c.syllable.word.utterance.speech_rate.column_name('utterance_speech_rate'),
                      c.syllable.speaker.name.column_name('speaker'),
                      c.syllable.discourse.name.column_name('file'),
                      )

With the above, we extract information of interest about the syllable, the word it is in, the utterance it is in, the
speaker and the sound file (``discourse`` in PolyglotDB's API).

To test out the query, we can ``limit`` the results (for readability) and print them:

.. code-block:: python

    # duplicated from above
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.stress == '1') # Stressed syllables...
        q = q.filter(c.syllable.begin == c.syllable.word.begin) # That are at the beginning of words...
        q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end) # that are at the end of utterances.

        q = q.columns(c.syllable.label.column_name('syllable'),
                      c.syllable.duration.column_name('syllable_duration'),
                      c.syllable.word.label.column_name('word'),
                      c.syllable.word.begin.column_name('word_begin'),
                      c.syllable.word.end.column_name('word_end'),
                      c.syllable.word.num_syllables.column_name('word_num_syllables'),
                      c.syllable.word.stress_pattern.column_name('word_stress_pattern'),
                      c.syllable.word.utterance.speech_rate.column_name('utterance_speech_rate'),
                      c.syllable.speaker.name.column_name('speaker'),
                      c.syllable.discourse.name.column_name('file'),
                      )

        q = q.limit(10)

        # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
        q = q.order_by(c.syllable.label)
        results = q.all()
        print(results)

Which will show the first ten rows that would be exported to a CSV file.

.. _tutorial_export:

Exporting a CSV file
====================

Once the query is constructed with filters and columns, exporting to a CSV file is a simple method call on the query object.
For completeness, the full code for the query and export is given below.

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.stress == '1')
        q = q.filter(c.syllable.begin == c.syllable.word.begin)
        q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end)

        q = q.columns(c.syllable.label.column_name('syllable'),
                      c.syllable.duration.column_name('syllable_duration'),
                      c.syllable.word.label.column_name('word'),
                      c.syllable.word.begin.column_name('word_begin'),
                      c.syllable.word.end.column_name('word_end'),
                      c.syllable.word.num_syllables.column_name('word_num_syllables'),
                      c.syllable.word.stress_pattern.column_name('word_stress_pattern'),
                      c.syllable.word.utterance.speech_rate.column_name('utterance_speech_rate'),
                      c.syllable.speaker.name.column_name('speaker'),
                      c.syllable.discourse.name.column_name('file'),
                      )

        q = q.order_by(c.syllable.label)
        q.to_csv(export_path)

The CSV file generated will then be ready to open in other programs or in R for data analysis. You can see a `full version of the script`_, as well as `expected output`_ when run on the 'LibriSpeech-subset' corpus.

Next steps
==========

Tutorials 4-6 show examples of acoustic analyses that can be performed on enriched corpora: adding vowel formants, pitch tracks, or using a custom Praat script.



Tutorials 1-3 are identical to :ref:`Case Study 1<case_study_duration>`.  See "Step 4" there for R code to visualize and analyze the exported results from Tutorial 3 (in ``tutorial_3_subset_output.csv``).
