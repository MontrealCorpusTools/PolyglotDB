
**************************
Encoding acoustic measures
**************************

PolyglotDB has some built-in functions to encode certain acoustic measures, and also supports encoding measures from a
Praat script. All of these functions carry out the acoustic analysis and save the results into the database. It
currently contains built-in functions to encode pitch, intensity, and formants.

In order to use any of them on your own computer, you must set your CorpusContext's :code:`config.praat_path` to point
to Praat, and likewise :code:`config.reaper_path` to Reaper if you want to use Reaper for pitch.

.. _pitch_encoding:

Encoding pitch
==============

Pitch is encoded using the :code:`analyze_pitch` function.

This is done as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_pitch()

.. note::

   The function :code:`analyze_pitch` requires that utterances be encoded prior to being run.
   See :ref:`enrichment_utterances` for further details on encoding utterances.

Following encoding, pitch tracks and summary statistics will be available for export for every annotation type.
See :ref:`track_measure_query` for more details.

Pitch analysis can be configured in two ways, the source program of the measurement and the algorithm for fine tuning the pitch range.

.. _pitch_sources:

Sources
-------

The keyword argument :code:`source` can be set to
either :code:`'praat'` or :code:`'reaper'`, depending on which program you would like PolyglotDB to use to measure pitch.
The default source is Praat.

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_pitch()
        # OR
        c.analyze_pitch(source='reaper')


If the source is `praat`, the Praat executable must be discoverable on the system path (i.e., a call of `praat` in a terminal works). Likewise, if the source is `reaper`, the Reaper executable must be on the path or the full path to the Reaper executable must be specified.


.. _pitch_algorithms:

Algorithms
----------

Similar to the `source`, attribute, the `algorithm` can be toggled between :code:`"base"`, :code:`"gendered"`, and :code:`"speaker_adapted"`.

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_pitch()

        # OR

        c.analyze_pitch(algorithm='gendered')

        # OR

        c.analyze_pitch(algorithm='speaker_adapted')

The :code:`"base"` algorithm uses a default minimum pitch of 50 Hz and a maximum pitch of 500 Hz, but these can be changed through the ``absolute_min_pitch`` and ``absolute_max_pitch`` parameters.

The :code:`"gendered"` algorithm checks whether a `Gender` property is available for speakers.  If a speaker has a property
value that starts with `f` (i.e., female),
utterances by that speakers will use a minimum pitch of 100 Hz and a maximum pitch of 500 Hz.  If they have a property
value of `m` (i.e., male),
utterances by that speakers will use a minimum pitch of 50 Hz and a maximum pitch of 400 Hz.

The :code:`"speaker_adapted"` algorithm does two passes of pitch estimation.  The first is identical to :code:`"base"`
and uses a minimum pitch of 50 Hz and a maximum pitch of 500 Hz (or whatever the parameters have been set to).
This first pass is used to estimate by-speaker means of F0.  Speaker-specific pitch floors and ceilings are calculated by adding or subtracting the number of octaves that the ``adjusted_octaves`` parameter specifies.  The default is 1, so the per-speaker pitch range will be one octave below and above the speaker's mean pitch.

.. _intensity_encoding:

Encoding intensity
==================

Intensity is encoded using :code:`analyze_intensity()`, as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_intensity()

.. note::

   The function :code:`analyze_intensity` requires that utterances be encoded prior to being run. See
   :ref:`enrichment_utterances` for further details on encoding utterances.

Following encoding, intensity tracks and summary statistics will be available for export for every annotation type.
See :ref:`track_measure_query` for more details.

.. _formant_encoding:

Encoding formants
=================

There are several ways of encoding formants.  The first is encodes formant tracks similar to encoding pitch or intensity
tracks (i.e., done over utterances).
There is also support for encoding formants tracks just over specified vowel segments.  
Finally, point measures of formants can be encoded.
Both formant tracks and points can be calculated using either just a simple one-pass algorithm 
or by using a multiple-pass refinement algorithm.

Basic formant tracks
--------------------

Formant tracks over utterances are encoded using :code:`analyze_formant_tracks`, as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_tracks()

.. note::

   The function :code:`analyze_formant_tracks` requires that utterances be encoded prior to being run. See
   :ref:`enrichment_utterances` for further details on encoding utterances.

Following encoding, formant tracks and summary statistics will be available for export for every annotation type. See
:ref:`track_measure_query` for more details.

Formant tracks can also be encoded just for specific phones by specifying a subset of phones:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_tracks(vowel_label='vowel')

.. note::

   This usage requires that a :code:`vowel` subset of phone types be already encoded in the database.
   See :ref:`enrichment_queries` for more details on creating subsets

These formant tracks do not do any specialised analysis to ensure that they are not false formants.

Basic formant point measurements
--------------------------------

The :code:`analyze_formant_points` function will generate measure for F1, F2, F3, B1, B2, and B3 at the time 
point 33% of the way through the vowel for every vowel specified.

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_points(vowel_label='vowel')

.. note::

   The function :code:`analyze_formant_points` requires that a :code:`vowel` subset of phone types be already encoded in the database.
   See :ref:`enrichment_queries` for more details on creating subsets


Refined formant points and tracks
---------------------------------

The other function for generating both point and track measurements is the :code:`analyze_formant_points_refinement`.  This function computes
formant measurementss for
multiple values of :code:`n_formants` from 4 to 7.  To pick the best measurement, the function initializes per-vowel
means and standard deviations with the :code:`F1, F2, F3, B1, B2, B3` values
generated by :code:`n_formants=5`.  Then, it performs multiple iterations that select the new best track as the one that
minimizes the Mahalanobis distance to the relevant prototype.
In order to choose whether you wish to save tracks or points in the database, just change the `output_tracks` parameter to `true` if you would 
like tracks, and `false` otherwise.
When operating over tracks, the algorithm still only evaluates the best parameters by using the 33% point. 

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_formant_points_refinement(vowel_label='vowel')

Following encoding, phone types that were analyzed will have properties for :code:`F1`, :code:`F2`, :code:`F3`,
:code:`B1`, :code:`B2`, and :code:`B3` available for query and export. See :ref:`point_measure_query` for more details.

.. _script_encoding:

Encoding Voice Onset Time(VOT) 
==============================

Currently there is only one method to encode Voice Onset Times(VOTs) into PolyglotDB.
This makes use of the `AutoVOT <https://github.com/mlml/autovot>`_ program which automatically calculates VOTs based on various acoustic properties.

VOTs are encoded over a specific subset of phones using :code: `analyze_vot` as follows:

.. code-block:: python

    with CorpusContext(config) as c:
        c.analyze_vot(self, classifier,
                    stop_label="stops",
                    vot_min=5,
                    vot_max=100,
                    window_min=-30,
                    window_max=30):

.. note::

   The function :code:`analyze_vot` requires that utterances and any subsets be encoded prior to being run. See
   :ref:`enrichment_utterances` for further details on encoding utterances and :ref:`enrichment_subsets` for subsets.

Parameters
----------
The :code: `analyze_vot` function has a variety of parameters that are important for running the function properly.
`classifier` is a string which has a paht to an AutoVOT classifier directory. 
A default classifier is available in `/tests/data/classifier/sotc_classifiers`.

`stop_label` refers to the name of the subset of phones that you intend to calculate VOTs for. 

`vot_min` and `vot_max` refer to the minimum and maximum duration of any VOT that is calculated. 
The `AutoVOT repo <https://github.com/mlml/autovot>` has some sane defaults for English voiced and voiceless stops.

`window_min` and `window_max` refer to the edges of a given phone's duration.
So, a `window_min` of -30 means that AutoVOT will look up to 30 milliseconds before the start of a phone for the burst, and
a `window_max` of 30 means that it will look up to 30 milliseconds after the end of a phone.

Encoding other measures using a Praat script
============================================

Other acoustic measures can be encoded by passing a Praat script to :code:`analyze_script`.

The requirements for the Praat script are:

* exactly one input: the full path to the sound file containing (only) the phone. (Any other parameters can be set manually
  within your script, and an existing script may need some other modifications in order to work on this type of input)
* print the resulting acoustic measurements (or other properties) to the Praat Info window in the following format:

  * The first line should be a space-separated list of column names. These are the names of the properties that will be
    saved into the database.
  * The second line should be a space-separated list containing one measurement for each property.
  * (It is okay if there is some blank space before/after these two lines.)

  An example of the Praat output::

    peak slope cog spread
    5540.7376 24.3507 6744.0670 1562.1936

  Output format if you are only taking one measure::

    cog
    6013.9

To run :code:`analyze_script`, do the following: 

1. encode a phone class for the subset of phones you would like to analyze
2. call :code:`analyze_script` on that phone class, with the path to your script

For example, to run a script which takes measures for sibilants:

.. code-block:: python

    with CorpusContext(config) as c:
        c.encode_class(['S', 'Z', 'SH', 'ZH'], 'sibilant')
        c.analyze_script('sibilant', 'path/to/script/sibilant.praat')
