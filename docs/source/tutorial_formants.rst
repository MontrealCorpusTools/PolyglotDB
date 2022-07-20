
.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_4_formants.py

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_4_subset_formants.csv

.. _vowel formant: https://en.wikipedia.org/wiki/Formant

.. _praat: https://www.fon.hum.uva.nl/praat/

.. _tutorial_formants:

***********************************
Tutorial 4: Vowel formant analysis
***********************************

The main objective of this tutorial is to perform `vowel formant`_ analysis on the enriched polyglot corpus we used in the previous three tutorials.

As in the other tutorials, import statements and the corpus name (as it is stored in pgdb) must be set for the code in this tutorial
to be runnable. The example given below continues to make use of the "tutorial-subset" corpus we have been using in tutorials 1-3.

.. code-block:: python

    from polyglotdb import CorpusContext

    # corpus_root = './data/LibriSpeech-aligned/'
    # corpus_name = 'tutorial'
    # export_path = './results/tutorial_4_formants.csv')
    corpus_root = './data/LibriSpeech-aligned-subset/'
    corpus_name = 'tutorial-subset'
    export_path = './results/tutorial_4_subset_formants.csv')

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

Now that all vowel syllables are isolated and easily queriable, polyglotdb can perform formant analysis on these vowels. The executbale run to perform formant analysis is configurable: a common option is to use `praat`_:

.. code-block:: python

  from polyglotdb import CorpusContext

  with CorpusContext(corpus_name) as c:
    c.config.praat_path = "/usr/bin/praat"
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
    results = q.all()
    q.to_csv(export_path)
