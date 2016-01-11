.. _pgdb_io:

**************
PolyglotDB I/O
**************

In addition to documenting the IO module of PolyglotDB, this document
should serve as a guide for implementing future importers for additional
formats.

Importers
=========

Importers to be used are either discourse importers (i.e, ``load_discourse_texgrid``)
or directory importers (i.e. ``load_directory_textgrid``).  Importing a
directory requires that all files in the directory have the same format.
For instance, TextGrids in a directory to import should have identical format, with
the same number of tiers, the same names of tiers, etc.

Currently there are the following importers:

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

Inspect functions (i.e. ``inspect_discourse_textgrid``) return guesses for
the types of annotations present in a given file (or files in a given
directory).  They return a list of AnnotationTypes, with the length depending
on aspects of the format.  For instance, the inspect function for TextGrids
will return an AnnotationType for each interval tier in the TextGrid.

Details of inspect functions
````````````````````````````

Textgrid:

- AnnotationType per interval tier
- The AnnotationType with the most number of intervals is guessed to be
  the one corresponding to segments
- The AnnotationType with the least number of intervals and closest to
  the first tier (top of the TextGrid in Praat) is guessed to be the
  word tier
- All interval tiers with the same number of intervals as the guessed
  word tier are guessed to be attributes of the words (i.e. part-of-speech)

.. note:: At the moment, the word guessing is most fragile.  Segments are
   generally guessed fairly accurately (unless a TextGrid is annotated with
   parts of segments).  A possible improvement would be to guess how many
   words should be in the TextGrid given the number of segments and some
   segment/word notion, so that larger annotations (like speaker, sentence, etc)
   are not improperly detected as words.

CSV:

- AnnotationType per column

Interlinear gloss files:

- Guesses the number of lines per gloss based on the number of words in
  each line (so 3 3 3 4 4 4, would return 3 lines per gloss with 2 total
  glosses and 2 2 2 2 3 3 would return 2 lines per gloss with 3 total glosses)
- AnnotationType per guessed number of lines per gloss
- First AnnotationType is guessed to be the orthography of the word
- Guesses the types of the remaining AnnotationTypes based on their content, i.e.,
  if they contain a ``.``, they are guessed to be a transcription.

Orthographic text files:

- One AnnotationType for the word

Transcribed text files:

- One AnnotationType for the word (with the property of having a transcription)

Buckeye:

- One AnnotationType for words
- Words have type properties for underlying transcription and token
  properties for their part of speech
- One AnnotationType for surface transcriptions

TIMIT:

- One AnnotationType for words
- One AnnotationType for surface transcriptions
- Timepoints in number of samples get converted to seconds

Format to DiscourseData
-----------------------

The lion's share of work gets done in functions that read the specific
format and output a DiscourseData object.  Their names are of the form
"format_to_data" (i.e. ``textgrid_to_data``).

These functions take a path to a file and a list of AnnotationTypes and
parse the file into a DiscourseData object.  Loading a DiscourseData object
into PolyglotDB is then straightforward.


Load discourse
--------------

Discourse loading functions are wrappers around the format-to-data functions
and calls to a CorpusContext's ``add_discourse`` function.

Load directory
--------------

Directory loading functions find all files matching the desired format
in the directory as well as subdirectories (corpora often have subdirectories
for each speaker).  For each such file, the function executes a similar
process to loading single discourses.

Exporters
=========

Needs work

Export discourse
----------------

Export directory
----------------

