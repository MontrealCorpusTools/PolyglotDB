

.. _lexicon_queries:

***************
Lexicon queries
***************

Querying the lexicon is in many ways similar to querying annotations in graphs.

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_lexicon(c.lexicon_phone).filter(c.lexicon_phone.label == 'aa')
       print(q.all())

The above query will just return one result (as there is only one phone type with a given label) as opposed to the multiple
results returned when querying annotations.
