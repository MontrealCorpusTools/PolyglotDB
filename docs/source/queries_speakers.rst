

.. _speaker_queries:

***************
Speaker queries
***************

Querying speaker information is similar to querying other aspects, and function very similarly to querying discourses.  Queries are constructed through the function :code:`query_speakers`:


.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_speakers()
       speakers = [x['name'] for x in q.all()]
       print(speakers)

The above code will print all of the speakers in the current corpus.  Like other queries, speakers can be filtered by properties that are encoded for them
and specific information can be extracted.


.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_speakers().filter(c.speaker.name == 'Speaker 1').columns(c.speaker.discourses.name.column_name('discourses'))
       speaker1_discourses = q.all()[0]['discourses']
       print(speaker1_discourses)

The above query will print out all the discourses that a speaker identified as ``"Speaker 1"`` spoke in.
