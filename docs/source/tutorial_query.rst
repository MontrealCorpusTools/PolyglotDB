
.. _Jupyter notebook: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_3_query.ipynb

.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial3.py

.. _related ISCAN tutorial: https://iscan.readthedocs.io/en/latest/tutorials_iscan.html#examining-analysing-the-data

.. _tutorial_query:

***********************************
Tutorial 3: Getting information out
***********************************

The main objective of this tutorial is to export a CSV file using a query on an imported (:ref:`tutorial_first_steps`) and
enriched (:ref:`tutorial_enrichment`) corpus.
This tutorial is available as a `Jupyter notebook`_ as well.

Creating an initial query
=========================

The first steps for generating a CSV file is to create a query that selects just the annotations of interest to our study.
In this case, we want all syllables that are `stressed` (defined here as having a ``stress`` value equal to ``'1'``), at the beginning of
words that are at the end of utterances.

.. code-block:: python

    with CorpusContext('pg_tutorial') as c:
        q = c.query_graph(c.syllable)

        q = q.filter(c.syllable.stress == '1') # Stressed syllables...
        q = q.filter(c.syllable.begin == c.syllable.word.begin) # That are at the beginning of words...
        q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end) # that are at the end of utterances.


Next, we want to specify the particular information to extract for each syllable found.


.. code-block:: python

        # ... continued from above

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

To test out the query, we can ``limit`` the results and print them:


.. code-block:: python

        # ... continued from above

        q = q.limit(10)
        results = q.all()
        print(results)

Which will show the first ten rows that would be exported to a csv.

.. _tutorial_export:

Exporting a CSV file
====================

Once the query is constructed with filters and columns, exporting to a CSV is a simple method call on the query object.
For completeness, the full code for the query and export is given below.

.. code-block:: python

    export_path = '/path/to/export/pg_tutorial.csv'

    with CorpusContext('pg_tutorial') as c:
        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.stress == 1)

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
        q.to_csv(export_path)

The CSV file generated will then be ready to open in other programs or in R for data analysis.

Next steps
==========

See the `related ISCAN tutorial`_ for R code on visualizing and analyzing the exported results.