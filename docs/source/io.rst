
.. _Montreal Forced Aligner: https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner

.. _FAVE-align: https://github.com/JoFrhwld/FAVE

.. _LaBB-CAT: http://labbcat.sourceforge.net/

.. _TIMIT: https://catalog.ldc.upenn.edu/LDC93S1

.. _Buckeye: https://buckeyecorpus.osu.edu/

.. _BAS Partitur: http://www.bas.uni-muenchen.de/forschung/publikationen/Granada-98-Partitur.pdf

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

- Praat TextGrids
- Output from forced aligners (`Montreal Forced Aligner`_ and `FAVE-align`_)
- Output from other corpus management software (`LaBB-CAT`_)
- Text files

  - Interlinear gloss text files
  - `BAS Partitur`_ format

- Corpus-specific formats

  - `Buckeye`_
  - `TIMIT`_

Inspect
-------

Inspect functions (i.e., :code:`inspect_textgrid`) return a guess for
how to parse the annotations present in a given file (or files in a given
directory).  They return a parser of the respective type (i.e., :code:`TextgridParser`)
with an attribute for the :code:`annotation_types` detected.  For instance, the inspect function for TextGrids
will return a parser with annotation types for each interval and point tier in the TextGrid.

Details of inspect functions
````````````````````````````

Textgrid (:ref:`io_tg_parser_api`):

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

  - Creates word type transcription property based off contained phones (if both exist)

LaBB-CAT format TextGrids (:ref:`io_labbcat_parser_api`):

- Annotation types:

  - One AnnotationType for words
  - One AnnotationType for phones

- Hierarchy:

  - Creates word type transcription property based off contained phones

MFA (:ref:`io_mfa_parser_api`):

- Annotation types:

  - One AnnotationType for words
  - One AnnotationType for phones

- Hierarchy:

  - Creates word type transcription property based off contained phones

Buckeye (:ref:`io_buckeye_parser_api`):

- Annotation types:

  - One AnnotationType for words
  - Words have type properties for underlying transcription and token
    properties for their part of speech
  - One AnnotationType for phones


TIMIT (:ref:`io_timit_parser_api`):

- Annotation types:

  - One AnnotationType for words
  - One AnnotationType for phones
  - Timepoints in number of samples get converted to seconds

- Hierarchy:

  - Creates word type transcription property based off contained phones


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

