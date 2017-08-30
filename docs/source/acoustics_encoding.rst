**************************
Encoding acoustic measures
**************************

PolyglotDB has some built-in functions to encode certain acoustic measures, and also supports encoding measures from a Praat script. All of these functions carry out the acoustic analysis and save the results into the database. It currently contains built-in functions to encode pitch, intensity, and formants (right?).

In order to use any of them on your own computer, you must set your CorpusContext's :code:`config.praat_path` to point to Praat, and likewise :code:`config.reaper_path` to Reaper if you want to use Reaper for pitch. (Currently, if you are on Windows your Praat program must also be re-named Praatcon.exe for acoustics to work- Michael should fix this in acousticsim)

Encoding pitch
==============

Pitch is encoded using :code:`analyze_pitch()`. Your CorpusContext's :code:`config.pitch_source` can be set to either :code:`'praat'` or :code:`'reaper'`, depending on which program you would like PolyglotDB to use to measure pitch.

This is done as follows:

.. code-block:: python

	with CorpusContext(config) as c:
		c.config.pitch_source = 'praat'
		c.analyze_pitch()

Encoding intensity
==================

Intensity is encoded using :code:`analyze_intensity()`, as follows:

.. code-block:: python

	with CorpusContext(config) as c:
		c.analyze_intensity()

Encoding formants
=================

Formants are encoded using :code:`analyze_formants()`, as follows:

.. code-block:: python

	with CorpusContext(config) as c:
		c.analyze_formants()

(TODO: I'm not sure how this has changed since May - Arlie has written new functions for formants. Looks like they are by phone now? (are utterance-level formants still possible??))

Formants can also be encoded on a per-phone basis using :code:`analyze_formants_vowel_segments_new`. (I don't know what to say about this or how exactly it works.)

Encoding other measures using a Praat script
============================================

Other acoustic measures can be encoded by passing a Praat script to :code:`analyze_script`.

The requirements for the Praat script are:

* exactly one input: the full path to the sound file containing (only) the phone. (Any other parameters can be set manually within your script, and an existing script may need some other modifications in order to work on this type of input)
* print the resulting acoustic measurements (or other properties) to the Praat Info window in the following format:

  * The first line should be a space-separated list of column names. These are the names of the properties that will be saved into the database.
  * The second line should be a space-separated list containing one measurement for each property.
  * (It is okay if there is some blank space before/after these two lines.)

  An example of the Praat output::

	peak slope cog spread
	5540.7376 24.3507 6744.0670 1562.1936

  Output format if you are only taking one measure::

	cog
	6013.9

To run :code:`analyze_script`, do the following: 

1. encode a phone class for the subset of phones you would like to analyze (CODING TODO: should I allow this to be null in order to run on all phones?)
2. call :code:`analyze_script` on that phone class, with the path to your script

For example, to run a script which takes measures for sibilants:

.. code-block:: python

	with CorpusContext(config) as c:
		c.encode_class(['S', 'Z', 'SH', 'ZH'], 'sibilant')
		c.analyze_script('sibilant', 'path/to/script/sibilant_jane.praat')