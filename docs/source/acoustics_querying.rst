.. _acoustics_querying:

**************************
Querying acoustic measures
**************************

Measures saved as tracks
========================

(TODO: better titles for subsections here)

All of the built-in acoustic measures are saved as tracks with 10-second intervals in the database (and formants created using :code:`analyze_formants_vowel_segments_new`??). To access these values, you use :code:`corpus_context.phone.MEASUREMENT.track`, replacing :code:`MEASUREMENT` with the name of the measurement you want: :code:`pitch`, :code:`formants`, or :code:`intensity`. 

Example: querying for formant track (TODO: I haven't tested whether this really works exactly as it's written)

.. code-block:: python

	with CorpusContext(config) as c:
		q = c.query_graph(c.phone)
		q = q.columns(c.phone.begin, c.phone.end, c.phone.formants.track)
		results = q.all()
		q.to_csv('path/to/output.csv')

You can also find the :code:`min`, :code:`max`, and :code:`mean` of the track for each phone, using :code:`corpus_context.phone.MEASUREMENT.min`, etc.

Measures saved not as tracks
============================

Anything encoded using :code:`analyze_script` is not saved as a track, and are instead recorded once for each phone. These are accessed using :code:`corpus_context.phone.MEASUREMENT`, replacing :code:`MEASUREMENT` with the name of the measurement you want.

Example: querying for :code:`cog` (center of gravity)

.. code-block:: python

	with CorpusContext(config) as c:
		q = c.query_graph(c.phone)
		q = q.columns(c.phone.begin, c.phone.end, c.phone.cog)
		results = q.all()
		q.to_csv('path/to/output.csv')