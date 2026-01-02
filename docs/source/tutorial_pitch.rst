
.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_5_pitch.py

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_5_subset_pitch.csv

.. _praat: https://www.fon.hum.uva.nl/praat/

.. _follow-up analysis: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_5_pitch.html

.. _rmd script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_5_pitch.Rmd

.. _tutorial scripts: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial

.. _tutorial_pitch:

***********************************
Tutorial 5: Pitch extraction
***********************************

The objective of this tutorial is to perform pitch (f0) extraction on the enriched PolyglotDB corpus we used in Tutorials 1-3.

The complete Python script for Tutorial 5 is available here: `tutorial scripts`_.


Workflow
========

**This tutorial assumes you have already run Tutorials 1 and 2**, which import and enrich the corpus with syllable, speaker, and utterance information.

Tutorial 5 can be followed in two ways, like other tutorials (see :ref:`here<tutorial_1_workflow>`):

* Pasting in commands one by one into the Python interpreter
* Running the entire script at once (``python tutorial_5.py``)

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

   import os
   import re
   from polyglotdb import CorpusContext

   # corpus_root = './data/LibriSpeech-aligned/'
   # corpus_name = 'tutorial'
   # export_path = './results/tutorial_4_formants.csv')
   corpus_root = './data/LibriSpeech-aligned-subset/'
   corpus_name = 'tutorial-subset'
   export_path = './results/tutorial_5_pitch.csv'

Vowel phoneme enrichment
=========================

In order to analyze pitch, vowel information needs to be encoded in our corpus. See the "Vowel phoneme enrichment" section in :ref:`tutorial_formants` to encode the required vowel information. If you have already completed tutorial 4, it is not necessary to repeat vowel encoding, and you can move on to the next step.

Pitch Encoding
=========================

To extract pitch tracks from the data, we first encode syllable count per word.

.. code-block:: python

  with CorpusContext(corpus_name) as c:
  c.encode_count('word', 'syllable', 'num_syllables')


Then, the CorpusContext method analyze_pitch is used with a configurable pitch analysis exectuble. Like tutorial 4, in this case, we use `praat`_:

.. note::
  When performing analysis with Praat, you might encounter an ``EOFError`` due to the use of multiprocessing by polyglotdb. To avoid this, include the statement: ``if __name__ == '__main__':`` at the beginning of your program.

.. code-block:: python

  with CorpusContext(corpus_name) as c:
  c.reset_acoustic_measure('pitch')
  c.config.praat_path = "/usr/bin/praat"
  metadata = c.analyze_pitch(algorithm='speaker_adapted', call_back=print)

Pitch is now encoded in all relevant vowels. The next step is to query the data for export.

Exporting a CSV file
==========================

We can now query the results using a similar set of commands as in the previous tutorials:

.. code-block:: python

  with CorpusContext(corpus_name) as c:
    # phone comes at beginning of utterance
    q = c.query_graph(c.phone).filter(c.phone.word.begin == c.phone.word.utterance.begin)

    # restrict just to phone = vowels
    q = q.filter(c.phone.subset == 'vowel')

    # preceding phone is at beginning of the word
    q = q.filter(c.phone.previous.begin == c.phone.word.begin)

    q = q.columns(c.phone.id.column_name('traj_id'),
                  c.phone.label.column_name('vowel'),
                  c.phone.previous.label.column_name('consonant'),
                  c.phone.following.label.column_name('following_phone'),
                  c.phone.word.label.column_name('word'),
                  c.phone.word.duration.column_name('word_duration'),
                  c.phone.word.transcription.column_name('word_transcription'),
                  c.phone.word.following.transcription.column_name('following_word_transcription'),
                  c.phone.begin.column_name('begin'),
                  c.phone.end.column_name('end'),
                  c.phone.discourse.name.column_name('discourse'),
                  c.phone.speaker.name.column_name('speaker'),
                  c.phone.speaker.sex.column_name('sex'),
                  c.phone.pitch.track.column_name('f0'))

    # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
    q = q.order_by(c.phone.label)
    results = q.all()
    q.to_csv(export_path)

The CSV file generated will then be ready to open in other programs or in R for data analysis. You can see a `full version of the script`_ and its `expected output`_ when run on the 'LibriSpeech-subset' corpora.


Next steps
===============
At this point, the corpus is ready for pitch analysis using R. We have provided an `rmd script`_ showcasing a possible approach, compiled
`here <https://html-preview.github.io/?url=https://github.com/MontrealCorpusTools/PolyglotDB/blob/main/examples/tutorial/results/tutorial_5_pitch.html>`_
(`source <https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_5_pitch.html>`_)
These results were found using the full LibriSpeech-aligned dataset,
which contains many more speakers than the subset we have been using in tutorials so far.



.. We have also provided results for running this script on the "LibriSpeech-aligned" (the full dataset) in a `follow-up analysis`_ html. These results contains many more speakers than the subset we have been using in tutorials so far to provide sufficient data for coherent analysis.

.. At this point, the corpus is ready for formant analysis using R.
.. We have provided an `rmd script`_ showcasing a possible approach, compiled
.. `here <https://html-preview.github.io/?url=https://github.com/MontrealCorpusTools/PolyglotDB/blob/main/examples/tutorial/results/tutorial_4_formants.html>`_ (`source <https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_formants.html>`_). We have also provided results for running this script in a  html.
.. These results were found using the full LibriSpeech-aligned dataset, which contains many more speakers than the subset we have been using in tutorials so far.


.. See :ref:`tutorial_formants` for another practical example of interesting linguistic analysis that can be peformed on enriched corpora using python and R.
