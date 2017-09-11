**************************
Encoding acoustic measures
**************************

PolyglotDB has some built-in functions to encode certain acoustic measures, and also supports encoding measures from a Praat script. All of these functions carry out the acoustic analysis and save the results into the database. It currently contains built-in functions to encode pitch, intensity, and formants (right?).

In order to use any of them on your own computer, you must set your CorpusContext's :code:`config.praat_path` to point to Praat, and likewise :code:`config.reaper_path` to Reaper if you want to use Reaper for pitch. (Currently, if you are on Windows your Praat program must also be re-named Praatcon.exe for acoustics to work- Michael should fix this in acousticsim)

.. _pitch_encoding:

Encoding pitch
==============

Pitch is encoded using the :code:`analyze_pitch` function.

This is done as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.config.pitch_source = 'praat'
        c.analyze_pitch()

.. note::

   The function :code:`analyze_pitch` requires that utterances be encoded prior to being run. See :ref:`enrichment_utterances` for further details on encoding utterances.

Following encoding, pitch tracks and summary statistics will be available for export for every annotation type. See :ref:`track_measure_query` for more details.

Pitch analysis can be configured in two ways, the source program of the measurement and the algorithm for fine tuning the pitch range.

.. _pitch_sources:

Sources
-------

Your CorpusContext's :code:`config.pitch_source` can be set to
either :code:`'praat'` or :code:`'reaper'`, depending on which program you would like PolyglotDB to use to measure pitch.

.. code-block:: python

    with CorpusContext(config) as c:
        c.config.pitch_source = 'praat'
        # or
        c.config.pitch_source = 'reaper'

        c.analyze_pitch()


If the source is `praat`, the Praat executable must either be discoverable on the system path (i.e., a call of `praat` in a terminal works) or
the full path to the executable must be specified in the config of the CorpusContext.

.. code-block:: python

    with CorpusContext(config) as c:
        c.config.pitch_source = 'praat'
        c.config.praat_path = '/path/to/praat'

        c.analyze_pitch()

Likewise, if the source is `reaper`, the Reaper executable must be on the path or the full path to the Reaper executable must be specified.

.. code-block:: python

    with CorpusContext(config) as c:
        c.config.pitch_source = 'reaper'
        c.config.reaper_path = '/path/to/reaper'

        c.analyze_pitch()


.. _pitch_algorithms:

Algorithms
----------

Similar to the `pitch_source`, attribute, the `pitch_algorithm` can be toggled between :code:`"base"`, :code:`"gendered"`, and :code:`"speaker_adapted"`.

.. code-block:: python

    with CorpusContext(config) as c:
        # set up to use reaper
        c.config.pitch_source = 'reaper'
        c.config.reaper_path = '/path/to/reaper'

        # set pitch algorithm

        c.config.pitch_algorithm = 'base'

        # or

        c.config.pitch_algorithm = 'gendered'

        # or

        c.config.pitch_algorithm = 'speaker_adapted'

        c.analyze_pitch()

The :code:`"base"` algorithm uses a minimum pitch of 55 Hz and a maximum pitch of 480 Hz.

The :code:`"gendered"` algorithm checks whether a `Gender` property is available for speakers.  If a speaker has a property value that starts with `f` (i.e., female),
utterances by that speakers will use a minimum pitch of 100 Hz and a maximum pitch of 480 Hz.  If they have a property value of `m` (i.e., male),
utterances by that speakers will use a minimum pitch of 55 Hz and a maximum pitch of 400 Hz.

The :code:`"speaker_adapted"` algorithm does two passes of pitch estimation.  The first is identical to :code:`"base"` and uses a minimum pitch of 55 Hz and a maximum pitch of 480 Hz.
This first pass is used to estimate by-speaker means and standard deviations of F0.  The mean and SD for each speaker is then used to generate per-speaker minimum and maximum pitch values.
The minimum pitch value is 3 standard deviations below the speaker mean, and the maximum pitch value is 3 standard deviations above the speaker mean.

.. _intensity_encoding:

Encoding intensity
==================

Intensity is encoded using :code:`analyze_intensity()`, as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_intensity()

.. note::

   The function :code:`analyze_intensity` requires that utterances be encoded prior to being run. See :ref:`enrichment_utterances` for further details on encoding utterances.

Following encoding, intensity tracks and summary statistics will be available for export for every annotation type. See :ref:`track_measure_query` for more details.

.. _formant_encoding:

Encoding formants
=================

There are several ways of encoding formants.  The first is encodes formant tracks similar to encoding pitch or intensity tracks (i.e., done over utterances).
There is also support for encoding formants tracks just over specified vowel segments.  Finally, point measures of formants
can be encoded using either just a simple one-pass algorithm or by using a multiple-pass refinement algorithm.

Formant tracks
--------------

Formant tracks over utterances are encoded using :code:`analyze_formant_tracks`, as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_tracks()

.. note::

   The function :code:`analyze_formant_tracks` requires that utterances be encoded prior to being run. See :ref:`enrichment_utterances` for further details on encoding utterances.

Following encoding, formant tracks and summary statistics will be available for export for every annotation type. See :ref:`track_measure_query` for more details.

Formant tracks can also be encoded just for specific phones via :code:`analyze_vowel_formant_tracks`:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_vowel_formant_tracks(vowel_inventory=['aa','iy', 'uw'])

.. note::

   The function :code:`analyze_vowel_formant_tracks` requires that a :code:`vowel` subset of phone types be already encoded in the database
   or a :code:`vowel_inventory` argument be specified (which will then have the :code:`vowel` subset encoded first).  See :ref:`enrichment_queries` for more
   details on creating subsets

Formant point measurements
--------------------------

There are two algorithms for encoding formant point measures for vowels are available.  The :code:`analyze_formant_points` function
will generate measure for F1, F2, F3, B1, B2, and B3 at the time point 33% of the way through the vowel for every vowel specified.

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_points(vowel_inventory=['aa','iy', 'uw'])

.. note::

   The function :code:`analyze_formant_points` requires that a :code:`vowel` subset of phone types be already encoded in the database
   or a :code:`vowel_inventory` argument be specified (which will then have the :code:`vowel` subset encoded first).  See :ref:`enrichment_queries` for more
   details on creating subsets

The other function for generating point measurements is the :code:`analyze_formant_points_refinement`.  This function computes formant measurementss for
multiple values of :code:`n_formants` from 4 to 7.  To pick the best measurement, the function initializes per-vowel means and standard deviations with the :code:`F1, F2, F3, B1, B2, B3` values
generated by :code:`n_formants=5`.  Then, it performs multiple iterations that select the new best track as the one that minimizes the Mahalanobis distance to the relevant prototype.

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_points_refinement(vowel_inventory=['aa','iy', 'uw'])

Following encoding, phone types that were analyzed will have properties for :code:`F1`, :code:`F2`, :code:`F3`, :code:`B1`, :code:`B2`, and :code:`B3` available for query and export. See :ref:`point_measure_query` for more details.

.. _script_encoding:

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