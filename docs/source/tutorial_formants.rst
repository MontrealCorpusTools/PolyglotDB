
.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_4_formants.py

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_subset_formants.csv

.. _vowel formant: https://en.wikipedia.org/wiki/Formant

.. _praat: https://www.fon.hum.uva.nl/praat/

.. _follow-up analysis: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_formants.html

.. _rmd script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_formants.Rmd

.. _related ISCAN tutorial: https://iscan.readthedocs.io/en/latest/tutorials_iscan.html#step-4-examining-analysing-the-data

.. _tutorial scripts: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial

.. _tutorial_formants:


***********************************
Tutorial 4: Vowel formant analysis
***********************************

The main objective of this tutorial is to perform `vowel formant`_ analysis on the enriched polyglot corpus we used in Tutorials 1-3.

The complete Python script for Tutorial  is available here: `tutorial scripts`_.


Workflow
========

**This tutorial assumes you have already run Tutorials 1 and 2**, which import and enrich the corpus with syllable, speaker, and utterance information.

Tutorial 4 can be followed in two ways, like other tutorials (see :ref:`here<tutorial_1_workflow>`):

* Pasting in commands one by one into the Python interpreter
* Running the entire script at once (``python tutorial_4.py``)

Running the whole script is the usual workflow for PolyglotDB, but the commands are shown one by one here to make it easier to follow along.

..    Different kinds of enrichment, corresponding to different
..    subsections of this section, can be performed in any order. For
..    example, speaker enrichment is independent of syllable encoding, so
..    you can perform either one before the other and the resulting
..    database will be the same. Within a section, however (i.e.,
..    :ref:`tutorial_syllable_enrichment`), the ordering of steps matters. For example, syllabic segments must be specified before
..    syllables can be encoded, because the syllable encoding algorithm
..    builds up syllables around syllabic phones.

As in previous tutorials, ``import`` statements and the location of the corpus (``corpus_root``) must be set for the code in this tutorial
to be runnable.  (You also need to make sure the directory where you will save the CSV file, here ``results/``, exists.)

.. code-block:: python

    from polyglotdb import CorpusContext
    import re

    # corpus_root = './data/LibriSpeech-aligned/'
    # corpus_name = 'tutorial'
    # export_path = './results/tutorial_4_formants.csv')
    corpus_root = './data/LibriSpeech-aligned-subset/'
    corpus_name = 'tutorial-subset'
    export_path = './results/tutorial_4_subset_formants.csv'

Vowel phoneme enrichment
=========================

Currently, the tutorial-subset corpus contains an entry for each phoneme. We can query all phonemes using the following commands:

.. code-block:: python

   with CorpusContext(corpus_name) as c:
    q = c.query_lexicon(c.lexicon_phone)
    q = q.order_by(c.lexicon_phone.label)
    q = q.columns(c.lexicon_phone.label.column_name('phone'))
    phone_results = q.all()
    phone_set = [x.values[0] for x in phone_results]


We can then isolate only the vowel phonemes using regular expressions:

.. code-block:: python

  non_speech_set = ['<SIL>', 'sil', 'spn']
  vowel_regex = '^[AEOUI].[0-9]'
  vowel_set = [re.search(vowel_regex, p).string for p in phone_set
              if re.search(vowel_regex, p) != None and p not in non_speech_set]

The corpus can then be enriched with syllables that have vowels as their nuclei:

.. code-block:: python

  with CorpusContext(corpus_name) as c:
    c.encode_type_subset('phone', vowel_set, 'vowel')

  with CorpusContext(corpus_name) as c:
    c.encode_syllables(syllabic_label='vowel')


Using Praat to measure verb formants
=========================

Now that all vowel syllables are isolated and easily queriable, PolyglotDB can perform formant analysis on these vowels. The executable run to perform formant analysis is configurable: a common option is to use `praat`_:

.. note::
  When performing analysis with Praat, you might encounter an ``EOFError`` due to the use of multiprocessing by PolyglotDB. To avoid this, include the statement: ``if __name__ == '__main__':`` at the beginning of your program.

.. code-block:: python

  # NOTE: the location of your praat executable depends on your operating system/installation.
  # By default:
  # Windows: "C:\Program Files\Praat.exe"
  # Mac: "/Applications/Praat.app/Contents/MacOS/Praat"
  # Linux: "/usr/bin/praat"
  # double check where praat is installed on your system and change the praat_path variable as required.
  praat_path = "/usr/bin/praat"
  with CorpusContext(corpus_name) as c:
    c.config.praat_path = praat_path
    c.analyze_formant_points(vowel_label='vowel', call_back=print)

This step will enrich the corpus with formant variables (F1, F2, F3) aassociated with each vowel phoneme in the corpus.


Exporting a CSV file
=========================

We can now query the results using a similar set of commands as in the previous tutorials:

.. code-block:: python

  with CorpusContext(corpus_name) as c:
    q = c.query_graph(c.phone).filter(c.phone.subset == 'vowel')
    q = q.columns(c.phone.speaker.name.column_name('speaker'), # speaker enrichment performed in tutorial 2
                  c.phone.speaker.sex.column_name('speaker_sex'),
                  c.phone.discourse.name.column_name('file'),
                  c.phone.utterance.speech_rate.column_name('speech_rate'),
                  c.phone.word.label.column_name('word'),
                  c.phone.label.column_name('phone'),
                  c.phone.previous.label.column_name('previous'),
                  c.phone.following.label.column_name('following'),
                  c.phone.begin.column_name('phone_start'),
                  c.phone.end.column_name('phone_end'),
                  c.phone.F1.column_name('F1'), # the columns enriched by praat
                  c.phone.F2.column_name('F2'),
                  c.phone.F3.column_name('F3'))

    # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
    q = q.order_by(c.phone.label)
    results = q.all()
    q.to_csv(export_path)


The CSV file generated will then be ready to open in other programs or in R for data analysis. You can see a `full version of the script`_, its `expected output`_ when run on the 'LibriSpeech-subset' corpora.


Next steps
==========
At this point, the corpus is ready for formant analysis using R.
We have provided an `rmd script`_ showcasing a possible approach, compiled
`here <https://html-preview.github.io/?url=https://github.com/MontrealCorpusTools/PolyglotDB/blob/main/examples/tutorial/results/tutorial_4_formants.html>`_ (`source <https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_formants.html>`_). We have also provided results for running this script in a  html.
These results were found using the full LibriSpeech-aligned dataset, which contains many more speakers than the subset we have been using in tutorials so far.

.. See :ref:`tutorial_pitch` for another practical example of interesting linguistic analysis that can be peformed on enriched corpora using python and R.

.. This You can also see the `related ISCAN tutorial`_ for R code on visualizing and analyzing the exported results.

In this tutorial we have used the simplest possible formant measurement algorithm to measure static formants (one measure per vowel token).
See :ref:`refined_formant_encoding` for a more accurate/slower option, and :ref:`case_study_vowel_dynamics` for workflows for *dynamic* formant analysis (one track per vowel token).
