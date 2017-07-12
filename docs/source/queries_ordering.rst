.. _ordering:

********
Ordering
********

The :code:`order_by` function is used to provide an ordering to the results of
a query.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label.in_(['r','l']))
       q = q.filter(c.phone.discourse == 'a_discourse')
       q = q.order_by(c.phone.begin)

       results = q.all()
       print(results)


The results for the above query will be ordered by the timepoint of the
annotation.  Ordering by time is most useful for when looking at single
discourses (as including multiple discourses in a query would invalidate the
ordering).

.. note:: In grouped aggregate queries, ordering is by default by the
   first :code:`group_by` attribute.  This can be changed by calling :code:`order_by`
   before evaluating with :code:`aggregate`.
