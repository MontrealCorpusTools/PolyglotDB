
.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_2.py

.. _tutorial scripts: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial

.. _tutorial_enrichment:

************************************
Tutorial 2: Adding extra information
************************************

Preliminaries
=============

The  objective of this tutorial is to enrich an already imported corpus (see :ref:`tutorial_first_steps`) with additional
information not present in the original audio and transcripts.  This additional information will then be used for creating
linguistically interesting queries in the next tutorial (:ref:`tutorial_query`).
All the enrichment files (``iscan_lexicon.csv`` and ``SPEAKERS.csv``) that we will use in this tutorial are already bundled in with the tutorial corpus.

The complete Python script for Tutorial 2 is available here: `tutorial scripts`_.


Workflow
========

This tutorial assumes you have already done Tutorial 1. Tutorial 2 can be followed in two ways, like Tutorial 1 (see :ref:`here<tutorial_1_workflow>`):

* Pasting in commands one by one into the Python interpreter
* Running the entire script at once (``python tutorial_2.py``)

Running the whole script is the usual workflow for PolyglotDB, but the commands are shown one by one here to make it easier to follow along.

.. note::

   Different kinds of enrichment, corresponding to different
   subsections of this section, can be performed in any order. For
   example, speaker enrichment is independent of syllable encoding, so
   you can perform either one before the other and the resulting
   database will be the same. Within a section, however (i.e.,
   :ref:`tutorial_syllable_enrichment`), the ordering of steps matters. For example, syllabic segments must be specified before
   syllables can be encoded, because the syllable encoding algorithm
   builds up syllables around syllabic phones.

As in Tutorial 1, ``import`` statements and the location of the corpus (``corpus_root``) must be set for the code in this tutorial
to be runnable:

.. code-block:: python

    import os
    from polyglotdb import CorpusContext

    ## CHANGE THIS PATH to the location of the corpus on your system
    corpus_root = './data/LibriSpeech-aligned-subset/'
    corpus_name = 'tutorial-subset'

    ## See the enrichment_data/ subdirectory in the tutorial directory to view examples of these files
    speaker_filename = "SPEAKERS.csv"
    stress_data_filename = "iscan_lexicon.csv"


.. _tutorial_syllable_enrichment:

Encoding syllables
==================

Creating syllable annotations requires two steps.

**Step 1: Specifying syllabic segments**

We first specify the subset of phones in the corpus that are syllabic segments and function as syllabic nuclei. In general these will be vowels, but can also include syllabic consonants.

Subsets in PolyglotDB are completely arbitrary sets of labels that speed up querying and allow for simpler references; see :ref:`enrichment_subsets` for more details.

.. code-block:: python

   syllabics = ["ER0", "IH2", "EH1", "AE0", "UH1", "AY2", "AW2", "UW1", "OY2", "OY1", "AO0", "AH2", "ER1", "AW1",
             "OW0", "IY1", "IY2", "UW0", "AA1", "EY0", "AE1", "AA0", "OW1", "AW0", "AO1", "AO2", "IH0", "ER2",
             "UW2", "IY0", "AE2", "AH0", "AH1", "UH2", "EH2", "UH0", "EY1", "AY0", "AY1", "EH0", "EY2", "AA2",
             "OW2", "IH1"]

    with CorpusContext(corpus_name) as c:
        c.encode_type_subset('phone', syllabics, 'syllabic')


The database now contains the information that each phone type above
("ER0", etc.) is a member of a subset called "syllabics".  Thus, each
phone token, which belongs to one of these phone types, is also a
syllabic.

**Step 2: Encoding syllables**

With the syllabic segments specified  in the phone
inventory, we create the syllable
annotations as follows:

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        c.encode_syllables(syllabic_label='syllabic')


The ``encode_syllables`` function uses a maximum onset algorithm based on all existing word-initial sequences of phones not
marked as ``syllabic`` in this case, and then maximizes onsets between syllabic phones.  As an example, something like
``astringent`` would have a phone sequence of ``AH0 S T R IH1 N JH EH0 N T``.  In any reasonably-sized corpus of English, the
list of possible onsets would in include ``S T R`` and ``JH``, but not ``N JH``, so the sequence would be syllabified as
``AH0 . S T R IH1 N . JH EH0 N T``.

.. note::

   See :ref:`enrichment_syllables` for more details on syllable enrichment.


.. _tutorial_utterance_enrichment:

Encoding utterances
===================

As with syllables, encoding utterances consists of two steps.

**Step 1: encoding non-speech**

When a corpus is first imported,
every annotation is treated as speech. There are typically "words" that are actually non-speech
elements within the transcript. We will encode these non-speech
labels like ``<SIL>`` as "pauses" and not actual speech sounds:

.. code-block:: python

    pause_labels = ['<SIL>']

    with CorpusContext(corpus_name) as c:
        c.encode_pauses(pause_labels)


(Note that in the tutorial corpus ``<SIL>`` happens to be the only
possible non-speech "word", but in other corpora there will probably
be others, so you'd use a different ``pause_labels`` list.)

**Step 2: encoding utterances**

The next step is to create the utterance annotations based on these pauses.

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        c.encode_utterances(min_pause_length=0.15)

The `min_pause_length` argument specifies how long (in seconds) a non-speech
element has to be to act as an utterance boundary. In many cases,
"pauses" that are short enough, such as those inserted by a forced
alignment error, are not good utterance boundaries (or just signal a
smaller unit than an "utterance").  Thus, we set the minimum pause length to 150 msec (0.15 seconds).

.. note::

   See :ref:`enrichment_utterances` for more details on encoding pauses and utterances.


.. _tutorial_speaker_enrichment:

Speaker enrichment
==================

Included in the tutorial corpus is a CSV containing speaker information (``SPEAKERS.csv``), namely their gender and their actual name rather
than the numeric code used in LibriSpeech. This information can be imported into the corpus as follows:

.. code-block:: python

    speaker_enrichment_path = os.path.join(corpus_root, 'enrichment_data', speaker_filename)

    with CorpusContext(corpus_name) as c:
        c.enrich_speakers_from_csv(speaker_enrichment_path)

Note that the CSV file could have an arbitrary name and location, in
general.  The command above assumes the name and location for the
tutorial corpus.

Once enrichment is complete, we can then query information and extract information about these characteristics of speakers.

.. note::

   See :ref:`enrich_speakers` for more details on enrichment from csvs.


.. _tutorial_stress_enrichment:

Stress enrichment
=================

.. important::

   Stress enrichment requires the :ref:`tutorial_syllable_enrichment` step has been completed.

Once syllables have been encoded, there are a couple of ways to encode the stress level of the syllable (i.e., primary stress,
secondary stress, or unstressed).  The way used in this tutorial will use a lexical enrichment file included in the tutorial
corpus.  This file has a field named ``stress_pattern`` that gives a pattern for the syllables based on the stress.  For
example, ``astringent`` will have a stress pattern of ``0-1-0``.

.. code-block:: python

    lexicon_enrichment_path = os.path.join(corpus_root, 'enrichment_data', stress_data_filename)

    with CorpusContext(corpus_name) as c:
        c.enrich_lexicon_from_csv(lexicon_enrichment_path)
        c.encode_stress_from_word_property('stress_pattern')

Following this enrichment step, words will have a type property of ``stress_pattern`` and syllables will have a token property
of ``stress`` that can be queried on and extracted.

.. note::

    See :ref:`stress_enrichment` for more details on how to encode stress, as well as how to add tone rather than stress information to syllables for tone languages.


.. _tutorial_additional_enrichment:

Additional enrichment
=====================

.. important::

   Speech rate enrichment requires that both the :ref:`tutorial_syllable_enrichment` and :ref:`tutorial_utterance_enrichment`
   steps have been completed.

One of the final enrichment in this tutorial is to encode speech rate onto utterance annotations. The speech rate measure used
here is going to to be syllables per second.

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        c.encode_rate('utterance', 'syllable', 'speech_rate')

Next we will encode the number of syllables per word:

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        c.encode_count('word', 'syllable', 'num_syllables')

Once the enrichments are complete, a token property of ``speech_rate`` will be available for query and export on utterance
annotations, as well as one for ``num_syllables`` on word tokens.

.. note::

   See :ref:`enrichment_hierarchical` for more details on encoding properties based on the rate/count/position of lower
   annotations (i.e., phones or syllables) within higher annotations (i.e., syllables, words, or utterances).


Next steps
==========

You can see a `full version of the script`_ which carries out all steps shown in code above.

See :ref:`tutorial_query` for the next tutorial covering how to create and export interesting queries using the information
enriched above.  See :ref:`enrichment` for a full list and example usage of the various enrichments possible in PolyglotDB.
