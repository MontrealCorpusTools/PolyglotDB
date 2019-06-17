.. _acoustics_querying:

**************************
Querying acoustic measures
**************************

.. _track_measure_query:

Querying acoustic tracks
========================

All of the built-in acoustic measures are saved as tracks with 10 ms intervals in the database (and formants created using one of the
functions in :ref:`formant_encoding`). To access these values, you use :code:`corpus_context.phone.MEASUREMENT.track`, replacing :code:`MEASUREMENT` with the name of the measurement you want: :code:`pitch`, :code:`formants`, or :code:`intensity`.

Example: querying for formant track (TODO: I haven't tested whether this really works exactly as it's written)

.. code-block:: python

	with CorpusContext(config) as c:
		q = c.query_graph(c.phone)
		q = q.columns(c.phone.begin, c.phone.end, c.phone.formants.track)
		results = q.all()
		q.to_csv('path/to/output.csv')

You can also find the :code:`min`, :code:`max`, and :code:`mean` of the track for each phone, using :code:`corpus_context.phone.MEASUREMENT.min`, etc.

.. _point_measure_query:

Querying acoustic point measures
================================

Acoustic measures that only have one measurement per phone are termed point measures and are accessed as regular properties of the annotation.


Anything encoded using :code:`analyze_script` is not saved as a track, and are instead recorded once for each phone. These are accessed using :code:`corpus_context.phone.MEASUREMENT`, replacing :code:`MEASUREMENT` with the name of the measurement you want.

Example: querying for :code:`cog` (center of gravity)

.. code-block:: python

	with CorpusContext(config) as c:
		q = c.query_graph(c.phone)
		q = q.columns(c.phone.begin, c.phone.end, c.phone.cog)
		results = q.all()
		q.to_csv('path/to/output.csv')

Querying Voice Onset Time
-------------------------

Querying voice onset time is done in the same method as acoustic point measures, however, the `vot` object itself has different measures associated with it.

So, you must also include what you would like from the `vot` measurement as shown below.

.. code-block:: python

	with CorpusContext(config) as c:
		q = c.query_graph(c.phone)
		q = q.columns(c.phone.vot.begin, c.phone.vot.end, c.phone.vot.confidence)
		results = q.all()
		q.to_csv('path/to/output.csv')
