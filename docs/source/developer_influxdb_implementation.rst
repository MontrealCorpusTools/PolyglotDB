
.. _InfluxDB documentation: https://docs.influxdata.com/influxdb/v1.7/

.. _InfluxDB query language: https://docs.influxdata.com/influxdb/v1.7/query_language/

.. _Conch: https://github.com/mmcauliffe/Conch-sounds

.. _influxdb_implementation:

***********************
InfluxDB implementation
***********************

This section details how PolyglotDB saves and structures data within InfluxDB.  InfluxDB is a NoSQL time series database,
with a SQL-like query language.

.. note::

   This section assumes a bit of familiarity with the `InfluxDB query language`_, which is largely based on SQL.
   See the `InfluxDB documentation`_ for more details and reference to other aspects of InfluxDB.

.. _influxdb_schema:

InfluxDB Schema
===============

Each measurement encoded (i.e., pitch, intensity, formants) will have a separate table in InfluxDB, similar to SQL.
When querying, the query will ``select`` columns from a a table (i.e., ``select * from "pitch"``).  Each row in InfluxDB
minimally has a ``time`` field, as it is a time series database.  In addition, each row will have queryable fields and tags, in InfluxDB parlance.
Tags can function as separate tables, speeding up queries, while fields are simply values that are indexed.
All InfluxDB tables will have three tags (these create different indices for the database and speed up queries) for
``speaker``, ``discourse``, and ``channel``.  The union of ``discourse`` (i.e., file name) and ``channel`` (usually 0, particularly for mono sound files)
along with the ``time`` in seconds will always give a unique acoustic time point, and indexing by ``speaker`` is crucial for PolyglotDB's algorithms.

.. note::

   The time resolution for PolyglotDB is at the millisecond level.  In general, I think having measurements every 10ms is
   a balanced time resolution for acoustic measures.  Increasing the time resolution will also increase the processing time
   for PolyglotDB algorithms, as well as the database size.  Time resolution is generally a property of the analyses done,
   so greater time resolution than 10 ms is possible, but not greater than 1 ms, as millisecond time resolution is hardcoded in the current code.
   Any time point will be rounded/truncated to the nearest millisecond.


In addition to these tags, there are several queryable fields which are always present in addition to the measurement fields.
First, the ``phone``, ``word``, ``syllable``(if syllable encoding has been performed for the corpus) for the time point are saved to allow for efficient aggregation across annotations.
Second, the ``utterance_id``for the time point is also saved.  The ``utterance_id`` is used for general querying, where each utterance's track for the
requested acoustic property is queried once and then cached for any further results to use without needing to query the
InfluxDB again.  For instance, a query on phone formant tracks might return 2000 phones.  Without the ``utterance_id``, there
would be 2000 look ups for formant tracks (each InfluxDB query would take about 0.15 seconds), but using the utterance-based caching,
the number of hits to the InfluxDB database would be a fraction (though the queries themselves would take a little bit longer).

.. note::

   For performance reasons internal to InfluxDB, ``phone``, ``syllable``, ``word``, and ``utterance_id`` are ``fields`` rather than ``tags``, because
   the cross of them with ``speaker``, ``discourse``, and ``channel`` would lead to an extremely large cross of possible tag
   combinations.  This mix of tags and fields has been found to be the most performant.

Finally, there are the actual measurements that are saved.  Each acoustic track (i.e., ``pitch``, ``formants``, ``intensity``)
can have multiple measurements.  For instance, a ``formants`` track can have ``F1``, ``F2``, ``F3``, ``B1``, ``B2``, and ``B3``,
which are all stored together on the same time point and accessed at the same time.  These measures are kept in the corpus
hierarchy in Neo4j.  Each measurement track (i.e. ``pitch``) will be a node linked to the corpus (see the example in :ref:`dev_hierarchy`).
That node will have each property listed along with its data type (i.e., ``F0`` is a ``float``).

Optimizations for acoustic measures
===================================

PolyglotDB has default functions for generating ``pitch``, ``intensity``, and ``formants`` tracks (see :ref:`influxdb_saving_ref` for specific examples
and :ref:`influxdb_low_level_saving` for more details on how they are implemented).  For implementing
future built in acoustic track analysis functions, one realm of optimization lays in the differently sampled files that
PolyglotDB generates.  On import, three files are generated per discourse at 1,200Hz, 11,000Hz, and 16,000Hz.  The intended
purpose of these files are for acoustic analysis of different kinds of segments/measurements.  The file at 1,200Hz is ideal
for pitch analysis (maximum pitch of 600Hz), the file at 11,000Hz is ideal for formant analysis (maximum formant frequency
of 5,500Hz).  The file at 16,000Hz is intended for consonantal analysis (i.e., fricative spectral analysis) or any other
algorithm requiring higher frequency information.  The reason these three files are generated is that analysis functions
generally include the resampling to these frequencies as part of the analysis, so performing it ahead of time can speed up
the analysis.  Some programs also don't necessarily include resampling (i.e., pitch estimation in REAPER), so using the
appropriate file can lead to massive speed ups.


.. _dev_acoustic_query:

Query implementation
====================

Given a PolyglotDB query like the following:

.. code-block:: python

    with CorpusContext('corpus') as c:
        q = c.query_graph(c.word)
        q = q.filter(c.word.label == 'some_word')
        q = q.columns(c.word.label.column_name('word'), c.word.pitch.track)
        results = q.all()


Once the Cypher query completes and returns results for a matching word, that information is used to create an InfluxDB
query.  The inclusion of an acoustic column like the pitch track also ensures that necessary information like the utterance ID
and begin and end time points of the word are returned.  The above query would result in several queries like the following being
run:

.. code-block:: sql

   SELECT "time", "F0" from "pitch"
   WHERE "discourse" = 'some_discourse'
   AND "utterance_id" = 'some_utterance_id'
   AND "speaker" = 'some_speaker'

The above query will get all pitch points for the utterance of the word in question, and create Python objects for the
track (:class:`polyglotdb.acoustics.classes.Track`) and each time point (:class:`polyglotdb.acoustics.classes.TimePoint`).
With the ``begin`` and ``end`` properties of the word, a slice of the track is added to the output row.

Aggregation
-----------

Unlike for aggregation of properties in the Neo4j database (see :ref:`dev_aggregation_query`), aggregation of acoustic
properties occurs in Python rather than being implemented in a query to InfluxDB, for the same performance reasons above.
By caching utterance tracks as needed, and then performing aggregation over necessary slices (i.e., words or phones), the
overall query is much faster.

Low level implementation
========================

.. _influxdb_low_level_saving:

Saving acoustics
----------------

The general pipeline for generating and saving acoustic measures is as follows:

- Acoustic analysis using Conch's analysis functions
- Format output from Conch into InfluxDB format and fill in any needed information (phone labels)
- Write points to InfluxDB
- Update the Corpus hierarchy with information about acoustic properties

Acoustic analysis is first performed in `Conch`_, a Python package for processing sound files into acoustic and auditory
representations.  To do so, segments are created in PolyglotDB through calls to :meth:`polyglotdb.acoustics.segments.generate_segments`
and related functions.  The generated ``SegmentMapping`` object from Conch is an iterable of ``Segment`` objects.  Each ``Segment`` minimally
has a path to a sound file, the begin time stamp, the end time stamp, and the channel.  With these four pieces of information,
the waveform signal can be extracted and acoustic analysis can be performed.  ``Segment`` objects can also have other
properties associated with them, so that the ``SegmentMapping`` can be grouped into sensible bits of analysis (``SegmentMapping.grouped_mapping()``.
This is done in PolyglotDB to split analysis by speakers, for instance.

``SegmentMapping`` and those returned by the ``grouped_mapping`` can then be passed to ``analyze_segments``, which in addition
to a ``SegmentMapping`` take a callable function that takes the minimal set of arguments above (file path, begin, end, and channel)
and return some sort of track or point measure from the signal segment.  Below for a list of generator functions that return
a callable to be used with ``analyze_segments``.  The ``analyze_segments`` function uses multiprocessing to apply the callable
function to each segment, allowing for speed ups for the number of available cores on the machine.

Once the Conch analysis function completes, the tracks are saved via :meth:`polyglotdb.corpus.AudioContext.save_acoustic_tracks`.
In addition to the ``discourse``, ``speaker``, ``channel``, and ``utterance_id``, ``phone`` label information is also added to each time
point's measurements.  These points are then saved using the ``write_points`` function of the ``InfluxDBClient``, returned
from the :meth:`~polyglotdb.corpus.AudioContext.acoustic_client` function.

.. _influxdb_saving_ref:

Reference functions
```````````````````

Hard-coded functions for saving acoustics are:

- :meth:`polyglotdb.acoustics.formants.base.analyze_formant_tracks`
- :meth:`polyglotdb.acoustics.intensity.analyze_intensity`
- :meth:`polyglotdb.acoustics.other.analyze_track_script`
- :meth:`polyglotdb.acoustics.pitch.base.analyze_pitch`
- :meth:`polyglotdb.acoustics.vot.base.analyze_vot`

Additionally, point measure acoustics analysis functions that don't involve InfluxDB (point measures are saved as Neo4j
properties):

- :meth:`polyglotdb.acoustics.formants.base.analyze_formant_points`
- :meth:`polyglotdb.acoustics.other.analyze_script`

Generator functions for Conch analysis:

- :meth:`polyglotdb.acoustics.formants.helper.generate_variable_formants_point_function`
- :meth:`polyglotdb.acoustics.formants.helper.generate_formants_point_function`
- :meth:`polyglotdb.acoustics.formants.helper.generate_base_formants_function`
- :meth:`polyglotdb.acoustics.intensity.generate_base_intensity_function`
- :meth:`polyglotdb.acoustics.other.generate_praat_script_function`
- :meth:`polyglotdb.acoustics.pitch.helper.generate_pitch_function`

Querying acoustics
------------------

In general, the pipeline for querying is as follows:

- Construct InfluxDB query string from function arguments
- Pass this query string to an ``InfluxDBClient``
- Iterate over results and construct a :class:`polyglotdb.acoustics.classes.Track` object

All audio functions, and hence all interface with InfluxDB, is handled through the :class:`polyglotdb.corpus.AudioContext`
parent class for the CorpusContext.  Any constructed InfluxDB queries will get executed through an ``InfluxDBClient``, constructed
in the :meth:`polyglotdb.corpus.AudioContext.acoustic_client` function, which uses the InfluxDB connection parameters
from the CorpusContext.  As an example, see
:class:`polyglotdb.corpus.AudioContext.get_utterance_acoustics`.  First, a InfluxDB client is constructed, then a query
string is formatted from the relevant arguments passed to ``get_utterance_acoustics``, and the relevant property names for the acoustic
measure (i.e., ``F1``, ``F2`` and ``F3`` for ``formants``, see :ref:`influxdb_schema` for more details).  This query string is then run via the
``query`` method of the InfluxDBClient.  The results are iterated over and a :class:`polyglotdb.acoustics.classes.Track` object
is constructed from the results and then returned.


Reference functions
```````````````````

- :meth:`polyglotdb.corpus.AudioContext.get_utterance_acoustics`
- :meth:`polyglotdb.corpus.AudioContext.get_acoustic_measure`
