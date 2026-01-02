

.. _discourse_queries:

*****************
Discourse queries
*****************

Discourses can also be queried, and function very similarly to speaker queries. Queries are constructed through the function :code:`query_discourses`:


.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_discourses()
       discourses = [x['name'] for x in q.all()]
       print(discourses)

The above code will print all of the discourses in the current corpus.  Like other queries, discourses can be filtered by properties that are encoded for them
and specific information can be extracted.


.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_discourses().filter(c.discourse.name == 'File 1').columns(c.discourse.speakers.name.column_name('speakers'))
       file1_speakers = q.all()[0]['speakers']
       print(file1_speakers)

The above query will print out all the speakers that spoke in the discourse identified as ``"File 1"``.
