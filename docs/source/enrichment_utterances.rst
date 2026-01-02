.. _enrichment_utterances:

************************
Creating utterance units
************************

Utterances are groups of words that are continuous in some sense.  The can be thought of as similar to interpausal units or chunks
in other work.  The basic idea is that there are intervals in which there are no speech, a subset of which count as breaks in speech
depending on the length of these non-speech intervals.

To encode utterances, there are two steps:

1. :ref:`encoding_pauses`
2. :ref:`encoding_utterances`


.. _encoding_pauses:

Encoding non-speech elements
============================

Non-speech elements in PolyglotDB are termed `pause`.  Pauses are encoded as follows:

.. code-block:: python

   nonspeech_words = ['<SIL>','<IVER>']
   with CorpusContext(config) as c:
        c.encode_pauses(nonspeech_words)

The function `encode_pauses` takes a list of word labels that should not be considered speech in a discourse and marks them as such.

.. note::

   Non-speech words can also be encoded through regular expressions, as in:

   .. code-block:: python

      nonspeech_words = '^[<[{].*'
      with CorpusContext(config) as c:
          c.encode_pauses(nonspeech_words)

   Where the pattern to be matched is any label that starts with `<` or `[`.

Once pauses are encoded, aspects of pauses can be queried, as follows:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.pause).filter(c.pause.discourse.name == 'one_discourse')
       print(q.all())

Additionally, word annotations can have previous and following pauses that can be found:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.word).columns(c.word.label,
                                          c.word.following_pause_duration.column_name('pause_duration'))
       print(q.all())



.. note::

   Once pauses are encoded, accessing an annotation's previous or following word via `c.word.previous` will skip over
   any pauses.  So for a string like `I <SIL> go...`, the previous word to the word `go` would be `I` rather than `<SIL>`.

.. _encoding_utterances:

Encoding utterances
===================

Once pauses are encoded, utterances can be encoded by specifying the minimum length of non-speech elements that count as
a break between stretches of speech.

.. code-block:: python

   with CorpusContext(config) as c:
        c.encode_utterances(min_pause_length=0.15)

.. note::

   The function `encode_utterances` can be given a keyword argument for `call_back`, which is a function like `print` that
   allows for progress to be output to the console.

Following encoding, utterances are available to queried and used as any other linguistic unit. For example, to get a list of
all the instances of words at the beginnings of utterances:


.. code-block:: python

   with CorpusContext(config) as c:
        q = c.query_graph(c.word).filter(c.word.begin == c.word.utterance.begin)
        print(q.all())
