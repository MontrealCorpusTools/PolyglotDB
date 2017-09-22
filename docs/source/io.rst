.. _pgdb_io:

**************
PolyglotDB I/O
**************

In addition to documenting the IO module of PolyglotDB, this document
should serve as a guide for implementing future importers for additional
formats.

Import pipeline
===============

Importing a corpus consists of several steps.  First, a file must be
inspected with the relevant inspect function (i.e., ``inspect_textgrid`` or
``inspect_buckeye``).  These functions generate Parsers for a given format
that allow annotations across many tiers to be coalesced into linguistic
types (word, segments, etc).

As an example, suppose a TextGrid has an interval tier for word labels,
an interval tier for phone labels, tiers for annotating stop information
(closure duration, bursts, VOT, etc).  In this case, our parser would want
to associate the stop information annotations with the phones (or rather a
subset of the phones), and not have them as a separate linguistic type.

Following inspection, the file can be imported easily using a CorpusContext's
``load`` function.  Under the hood, what happens is the Parser object creates
standardized linguistic annotations from the annotations in the text file,
which are then imported into the database.

Currently the following formats are supported:

- TextGrid
- Column-delimited text files (i.e. CSV)
- Text files

  - Interlinear gloss text files
  - Orthographic text
  - Transcribed text

- Corpus-specific formats

  - Buckeye
  - TIMIT

Inspect
-------

Inspect functions (i.e., :code:`inspect_textgrid`) return a guess for
how to parse the annotations present in a given file (or files in a given
directory).  They return a parser of the respective type (i.e., :code:`TextgridParser`)
with an attribute for the :code:`annotation_types` detected.  For instance, the inspect function for TextGrids
will return a parser with annotation types for each interval and point tier in the TextGrid.

Details of inspect functions
````````````````````````````

Textgrid:

- Annotation types:

  - AnnotationType per tier
  - All interval tiers with the same number of intervals as the guessed
    word tier are guessed to be attributes of the words (i.e. part-of-speech)

.. note:: The linguistic types of annotation types (i.e., does a given
   annotation type contain an attribute of a word or a segment?)) is guessed
   via the rate/duration of the annotations in a tier.  Using average durations
   per discourse from the Buckeye Corpus, probability of the tier being a
   word or segment annotation is calculated and the higher probability determines
   the guess.  Currently the only guesses for linguistic types are "words"
   and "segments".

- Hierarchy:

  - Posits segments as contained by words (if both exist)

CSV:

- Annotation types:

  - AnnotationType per column

- Hierarchy:

  - Words only

Interlinear gloss files:

- Annotation types:

  - Guesses the number of lines per gloss based on the number of words in
    each line (so 3 3 3 4 4 4, would return 3 lines per gloss with 2 total
    glosses and 2 2 2 2 3 3 would return 2 lines per gloss with 3 total glosses)
  - AnnotationType per guessed number of lines per gloss
  - First AnnotationType is guessed to be the orthography of the word
  - Guesses the types of the remaining AnnotationTypes based on their content, i.e.,
    if they contain a ``.``, they are guessed to be a transcription.

- Hierarchy:

  - Words only

Orthographic text files:

- Annotation types:

  - One AnnotationType for the word

- Hierarchy:

  - Words only

Transcribed text files:

- Annotation types:

  - One AnnotationType for the word (with the property of having a transcription)

- Hierarchy:

  - Words only

Buckeye:

- Annotation types:

  - One AnnotationType for words
  - Words have type properties for underlying transcription and token
    properties for their part of speech
  - One AnnotationType for surface transcriptions

- Hierarchy:

  - Posits ``surface_transcriptions`` as contained by words

TIMIT:

- Annotation types:

  - One AnnotationType for words
  - One AnnotationType for surface transcriptions
  - Timepoints in number of samples get converted to seconds

- Hierarchy:

  - Posits ``surface_transcriptions`` as contained by words

Load discourse
--------------

Loading of discourses is done via a CorpusContext's ``load`` function:

.. code-block:: python

   import polyglotdb.io as pgio

   parser = pgio.inspect_textgrid('/path/to/textgrid.TextGrid')

   with CorpusContext(config) as c:
       c.load(parser, '/path/to/textgrid.TextGrid')

Alternatively, ``load_discourse`` can be used with the same arguments.
The ``load`` function automatically determines whether the input path to
be loaded is a single file or a folder, and proceeds accordingly.

Load directory
--------------

As stated above, a CorpusContext's ``load`` function will import a directory of
files as well as a single file, but the ``load_directory`` can be explicitly
called as well:

.. code-block:: python

   import polyglotdb.io as pgio

   parser = pgio.inspect_textgrid('/path/to/textgrids')

   with CorpusContext(config) as c:
       c.load_directory(parser, '/path/to/textgrids')

Exporters
=========

Under development.

