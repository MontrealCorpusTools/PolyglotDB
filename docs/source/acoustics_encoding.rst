.. _FastTrack: https://github.com/santiagobarreda/FastTrack

.. _AutoVOT:  https://github.com/mlml/autovot

.. _VoiceSauce: https://www.phonetics.ucla.edu/voicesauce/

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


.. _refined_formant_encoding:

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
This makes use of the `AutoVOT`_ program which automatically calculates VOTs based on various acoustic properties.

VOTs are encoded over a specific subset of phones using :code:`analyze_vot` as follows:

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
The :code:`analyze_vot` function has a variety of parameters that are important for running the function properly.
`classifier` is a string which has a paht to an AutoVOT classifier directory.
A default classifier is available in `/tests/data/classifier/sotc_classifiers`.

`stop_label` refers to the name of the subset of phones that you intend to calculate VOTs for.

`vot_min` and `vot_max` refer to the minimum and maximum duration of any VOT that is calculated.
The `AutoVOT repo <https://github.com/mlml/autovot>` has some sane defaults for English voiced and voiceless stops.

`window_min` and `window_max` refer to the edges of a given phone's duration.
So, a `window_min` of -30 means that AutoVOT will look up to 30 milliseconds before the start of a phone for the burst, and
a `window_max` of 30 means that it will look up to 30 milliseconds after the end of a phone.

.. _custom_script_encoding:

Encoding other measures using a Praat script
============================================

You can encode additional acoustic measures by passing a Praat script to either
:code:`analyze_script` or :code:`analyze_track_script`. It is essential to follow the exact input and output format for
your Praat script to ensure compatibility with the system.

- :code:`analyze_script`: Designed for single-point measurements. This function works for user-specific
  measurements that occur at exactly one point in time for any target annotation type
  (or a defined subset of that type) in the hierarchy, such as a predefined set of vowels within all phones.

- :code:`analyze_track_script`: Use this for continuous measurements or when measurements are required
  at multiple time points per annotation. This function allows you to configure your Praat script to
  output results for multiple time points.

analyze_script
--------------

There are two input formats available for designing your Praat script:

Format 1:
~~~~~~~~~
This is sufficient for most use cases and should be your default choice unless runtime efficiency is critical.
In this format, the system generates temporary sound files, each containing one instance of your chosen annotation type.

**Input Requirements:**

- One required input: the full path to the sound file. This input will be automatically filled by the system. You can define additional attributes as needed.

Example Praat script using Format 1 can be found `here <https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/praat_scripts/mean_pitch.praat>`_.
This script computes the mean F0 (pitch) over a sound file.

Format 2 (for optimized analysis):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This format is more efficient as it reuses the same discourse sound file for all annotations in the same discourse, avoiding the creation of extra files.

**Input Requirements:**

- Five required inputs:
    - Full path to the **long** sound file
    - `begin` time
    - `end` time
    - `channel`
    - `padding`

Do not assign values to these five fields; the system will populate them during processing. You may include additional
attributes beyond these five, but ensure that values are passed as an array via the API.

Example Praat script using Format 2 can be found `here <https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/praat_scripts/mean_pitch_optimized.praat>`_.
Similar to the previous example script, this script computes the mean F0 (pitch) over a sound file, but this time includes the extra four inputs.

**Key Notes:**

- Always use :code:`Open long sound file` to ensure compatibility with the system.
- Must manually extract the segment within the script using the `begin`` and `end` inputs.
- The `padding` field allows flexibility by extending the actual begin and end times of the segment (default is 0).
- Channel indexing starts at 0 in the system, so increment by 1 for use in Praat (Praat uses 1-based indexing).

**Output Requirements:**

- Print results to the Praat Info window in this format:
    - The first line contains space-separated column names (property names to be saved in the database).
    - The second line contains space-separated measurements for each property.

An example of the Praat output::

    peak slope cog spread
    5540.7376 24.3507 6744.0670 1562.1936

Output format if you are only taking one measure::

    cog
    6013.9

To run :code:`analyze_script`, follow these steps:

    1. (Optional) Encode a subset for the annotation type you want to analyze.
    2. Call :code:`analyze_script` with the annotation type, the subset name and the path to your script.

.. code-block:: python

    with CorpusContext(config) as c:
        # Defines a subset of phones called "sibilant"
        c.encode_type_subset('phone', ['S', 'Z', 'SH', 'ZH'], 'sibilant')

        # Uses a praat script that takes as input a filename and begin/end time, and outputs measures we'd like to take for sibilants
        # The analyze_script call then applies this script to every phone of type "sibilant" in the corpus.
        c.analyze_script(subset='sibilant', annotation_type="phone", script_path='path/to/script/sibilant.praat')


analyze_track_script
--------------------

This function shares the same input formats and functionality as :code:`analyze_script`. However,
:code:`analyze_track_script` is specifically designed for continuous measurements.
Before using this functionality, you must add utterance encoding. When calling the API, you will
need to specify an annotation type (e.g., phone, syllable, or word) to perform the analysis.
The script will then run separately for each instance of the selected annotation type in a multiprocessing manner.

**Output Requirements:**

- Print results to the Praat Info window in the following format:
    - The first line begins with time, followed by space-separated column names.
    - Subsequent lines contain timestamps and measurements for each property.

Example output::

    time    H1_A1  H1_A2  H1_A3  H1_H2
    0.242   1.378   -4.326  14.369  8.522
    0.277   -3.169  -10.276 9.383   3.002
    0.312   -0.217  -4.195  3.497   7.215


.. code-block:: python

    with CorpusContext(config) as c:
        script_path = 'voice_quality.praat'
        c.config.praat_path = '/path/to/your/praat/executable'
        props = [('H1_H2', float), ('H1_A1',float), ('H1_A2',float), ('H1_A3',float)]
        c.analyze_track_script('voice_quality', props, script_path, annotation_type='phone')

A detailed example of using this functionality for voice quality analysis, along with a sample Praat script, is provided in the tutorial. See (:ref:`tutorial_vq`) for more details.

Encoding acoustic tracks from CSV
=================================

Sometimes you may want to use external software to generate measurement tracks. Examples include:

    - F0 (pitch) tracks computed by an external library, across entire files
    - Voice quality tracks for each vowel, computed using `VoiceSauce`_
    - Vowel formant tracks, e.g. using `FastTrack`_.

If you have generated tracks using other software, you can import them into PolyglotDB using the functions :code:`save_track_from_csvs` and :code:`save_track_from_csv` as long as the files
follow the expected structure.

CSV Format::

    time, measurement1, measurement2, measurement3, ...

Additionally, the file name should match the name of the discourse for which the track should be saved.

Calling the function :code:`save_track_from_csv` with the file path will save the track. You must also provide a list of the columns that the system should read. It is assumed that all columns are of type float.

To load multiple CSV files at once, pass a directory path to :code:`save_track_from_csvs`.

**Example** (FastTrack output):

.. image:: images/fasttrack_csvoutput.png
   :width: 600

To load all the measures from the generated tracks:

.. code-block:: python

    with CorpusContext(config) as c:
        # loading one file
        c.save_track_from_csv('formants', '/path/to/csv', ['f1','b1','f2','b2','f3','b3','f1p','f2p','f3p','f0','intensity','harmonicity'])
        # loading multiple csv files
        c.save_track_from_csvs('formants', '/path/to/directory', ['f1','b1','f2','b2','f3','b3','f1p','f2p','f3p','f0','intensity','harmonicity'])


Encoding acoustic track statistics
==================================

After encoding an acoustic track measurement—either through the built-in algorithms or custom Praat scripts—
you can perform statistical aggregation on these data tracks. The supported statistical measures are: mean, median,
standard deviation (stddev), sum, mode, and count.

Aggregation can be performed on a specified annotation type, such as phones, words, or syllables
(if syllable encoding is available). The aggregation is conducted for all annotations with the same label.

Aggregation can be performed by speaker, in which case the results will be grouped by speaker,
and each (annotation_label, speaker) pair will have its corresponding statistical measure computed.

Once encoded, the computed statistics are stored and can be queried later.

.. code-block:: python

    with CorpusContext(config) as c:
        # Encode a statistic for an acoustic measure
        c.encode_acoustic_statistic('voice_quality', 'mean', by_annotation='phone', by_speaker=True)

        # Alternatively, call the get function directly; it will encode the statistic if not already available
        results = c.get_acoustic_statistic('voice_quality', 'mean', by_annotation='phone', by_speaker=True)
        # This would compute, save, and return the mean values for all voice quality measurements on a by speaker and by phone basis.
        # for example ('speaker1', 'AO1'): [1.4283178345991416, 5.21375241700153, 28.8672225446156, 18.57861883658481]
