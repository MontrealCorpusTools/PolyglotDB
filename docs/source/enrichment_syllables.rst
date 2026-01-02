.. _enrichment_syllables:

***********************
Creating syllable units
***********************

Syllables are groupings of phones into larger units, within words. PolyglotDB enforces a strict hierarchy, with the boundaries
of words aligning with syllable boundaries (i.e., syllables cannot stretch across words).

At the moment, only one algorithm is supported (`maximal onset`) because its simplicity lends it to be language agnostic.

To encode syllables, there are two steps:

1. :ref:`encoding_syllabics`
2. :ref:`encoding_syllables`


.. _encoding_syllabics:

Encoding syllabic segments
==========================

Syllabic segments are called via a specialized function:



.. code-block:: python

   syllabic_segments = ['aa', 'ae','ih']
   with CorpusContext(config) as c:
        c.encode_syllabic_segments(syllabic_segments)


Following this code, all phones with labels of `aa, ae, ih` will belong to the subset `syllabic`.  This subset can be
then queried in the future, in addition to allowing syllables to be encoded.

.. _encoding_syllables:

Encoding syllables
==================

.. code-block:: python

   with CorpusContext(config) as c:
        c.encode_syllables()

.. note::

   The function `encode_syllables` can be given a keyword argument for `call_back`, which is a function like `print` that
   allows for progress to be output to the console.

Two algorithms are available for encoding syllables: `maximal onset` (default) and `probabilistic`.
You can restrict the allowed onsets by passing a set of phone tuples to the `custom_onsets` keyword argument.For example, to allow only
`[B, D, G]` as onsets, you would call:

.. code-block:: python

   with CorpusContext(config) as c:
        c.encode_syllables(custom_onsets={('B',), ('D',), ('G',)})

The maximal onset algorithm automatically marks any word-initial non-syllabic cluster as a syllable onset.
This means you do not need to manually include onsets that typically occur only at the beginnings of words
and may otherwise cause incorrect syllable boundary placement — for example, ('S', 'T') or ('S', 'P') in English.
Following encoding, syllables are available to queried and used as any other linguistic unit. For example, to get a list of
all the instances of syllables at the beginnings of words:


.. code-block:: python

   with CorpusContext(config) as c:
        q = c.query_graph(c.syllable).filter(c.syllable.begin == c.syllable.word.begin)
        print(q.all())

.. _stress_tone:

Encoding syllable properties from syllabics
===========================================

Often in corpora there is information about syllables contained on the vowels.  For instance, if the transcription contains
stress levels, they will be specified as numbers 0-2 on the vowels (i.e. as in Arpabet).  Tone is likewise similarly encoded
in some transcription systems.  This section details functions that strip this information from the vowel and place it on
the syllable unit instead.

.. note::

   Removing the stress/tone information from the vowel makes queries easier, as getting all `AA` tokens no longer requires
   specifying that the label is in the set of `AA1, AA2, AA0`.  This functionality can be disabled by specifying `clean_phone_label=False`
   in the two functions that follow.

.. _stress_enrichment:

Encoding stress
---------------

.. code-block:: python

   with CorpusContext(config) as c:

        c.encode_stress_to_syllables()

.. note::

   By default, stress is taken to be numbers in the vowel label (i.e., `AA1` would have a stress of `1`).  A different
   pattern to use for stress information can be specified through the optional `regex` keyword argument.


.. _tone_enrichment:

Encoding tone
-------------

.. code-block:: python

   with CorpusContext(config) as c:

        c.encode_tone_to_syllables()

.. note::

   As for stress, a different regex can be specified with the `regex` keyword argument.
