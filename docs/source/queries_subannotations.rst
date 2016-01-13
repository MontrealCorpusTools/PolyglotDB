

.. _subannotations:


**************
Subannotations
**************

Annotations can have subannotations associated with them.  Subannotations
are not independent linguistic types, but have more information associated
with them than just a single property.  For instance, voice onset time (VOT)
would be a subannotation of stops (as it has a begin time and an end time
that are of interest).  Querying such subannotations would be performed as follows:


.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone)
       q = q.columns(c.phone.vot.duration.column_name('vot'))

       results = q.all()
       print(results)

In some cases, it may be desirable to have more than one subannotation of
the same type associated with a single annotation.  For instance,
voicing during the closure of a stop can take place at both the beginning
and end of closure, with an unvoiced period in the middle.  Using a similar
query as above would get the durations of each of these (in the order of
their begin time):


.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone)
       q = q.columns(c.phone.voicing_during_closure.duration.column_name('voicing'))

       results = q.all()
       print(results)

In some cases, we might like to know the total duration of such subannotations,
rather than the individual durations.  To query that information, we can
use an ``aggregate``:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone)
       results = q.aggregate(Sum(c.phone.voicing_during_closure.duration).column_name('total_voicing'))

       print(results)
