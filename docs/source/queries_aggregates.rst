.. _aggregates_and_groups:

*********************
Aggregates and groups
*********************

Aggregate functions are available in :code:`polyglotdb.graph.func`.  Aggregate
functions available are:

* Average
* Count
* Max
* Min
* Stdev
* Sum

In general, these functions take a numeric attribute as an argument.  The
only one that does not follow this pattern is :code:`Count`.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')

       result = q.aggregate(Count())
       print(result)


Like the :code:`all` function, :code:`aggregate` triggers evaluation of the query.
Instead of returning rows, it will return a single number, which is the
number of rows matching this query.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')

       result = q.aggregate(Average(c.phone.duration))
       print(result)


The above aggregate function will return the average duration for all 'aa'
phones followed by 'r' phones.

Aggregates are particularly useful with grouping.  For instance:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label.in_(['r','l']))
       q = q.group_by(c.phone.following.label.column_name('following_label'))

       result = q.aggregate(Average(c.phone.duration), Count())
       print(result)


The above query will return the average duration and the count of 'aa'
phones grouped by whether they're followed by an 'r' or an 'l'.

.. note:: In the above example, the :code:`group_by` attribute is supplied with
   an alias for output.  In the print statment and in the results, the column
   will be called 'following_label' instead of the default (more opaque) one.
