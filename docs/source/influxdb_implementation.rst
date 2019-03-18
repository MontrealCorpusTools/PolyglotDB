
.. _InfluxDB documentation: https://docs.influxdata.com/influxdb/v1.7/

.. _influxdb_implementation:

***********************
InfluxDB implementation
***********************

This section details how PolyglotDB saves and structures data within InfluxDB.  InfluxDB is a NoSQL time series database,
with a SQL-like query language.

.. note::

   This section assumes a bit of familiarity with the InfluxDB query language, see the `InfluxDB documentation`_ for
   more details and reference.


Database Schema
===============

All InfluxDB tables will have three tags (these create different indices for the database and speed up queries) for
``speaker``, ``discourse``, and ``channel``.  The union of ``discourse`` and ``channel`` along with the ``time`` in seconds
will always give a unique acoustic time point, and indexing by ``speaker`` is crucial for PolyglotDB's algorithms.

.. note::

   The time resolution for PolyglotDB is at the millisecond level.  In general, I think having measurements every 10ms is
   a balanced time resolution for acoustic measures.  Increasing the time resolution will also increase the processing time
   for PolyglotDB algorithms, as well as the database size.

In addition to these tags, there are several queryable fields which are always present in addition to the measurement fields.
First, the ``phone`` for the time point is saved to allow for efficient aggregation across phones.  Second, the ``utterance_id``
for the time point is also saved.  The ``utterance_id`` is used for general querying, where each utterance's track for the
requested acoustic property is queried once and then cached for any further results to use without needing to query the
InfluxDB again.  For instance, a query on phone formant tracks might return 2000 phones.  Without the ``utterance_id``, there
would be 2000 look ups for formant tracks (each InfluxDB query would take about 0.15 seconds), but using the utterance-based caching,
the number of hits to the InfluxDB database would be a fraction (though the queries themselves would take a little bit longer).

.. note::

   For performance reasons internal to InfluxDB, ``phone`` and ``utterance_id`` are ``fields`` rather than ``tags``, because
   the cross of them with ``speaker``, ``discourse``, and ``channel`` would lead to an extremely large cross of possible tag
   combinations.  This mix of tags and fields has been found to be the most performant.

Finally, there are the actual measurements that are saved.  Each acoustic track (i.e., ``pitch``, ``formants``, ``intensity``)
can have multiple measurements.  For instance, a ``formants`` track can have ``F1``, ``F2``, ``F3``, ``B1``, ``B2``, and ``B3``,
which are all stored together on the same time point and accessed at the same time.  These measures are kept in the corpus
hierarchy in Neo4j.  Each measurement track (i.e. ``pitch``) will be a node linked to the corpus (see the example in :ref:`dev_hierarchy`).
That node will have each property listed along with its data type (i.e., ``F0`` is a ``float``).

Optimizations for acoustic measures
===================================

PolyglotDB has default functions for generating ``pitch``, ``intensity``, and ``formants`` tracks.  For implementing
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