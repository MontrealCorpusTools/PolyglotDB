.. _graph_queries:

****************
Querying corpora
****************

Queries are the primary function of PolyglotDB.  In general, the API provided
should cover all the usual questions that a phonetician might have about
a corpus.

.. note:: See :code:`examples/buckeye_querying.py` for some example queries in
   the Buckeye corpus.


.. _basic_queries:

Basic structural queries
========================

The main way of accessing discourses is through the :code:`query_graph` method of
:code:`CorpusContext` objects.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.word).filter(c.word.label == 'are')
       print(q.all())

The above code will find and print all instances of :code:`word` annotations that are
labeled with 'are'.  The method :code:`query_graph` takes one argument, which is
an attribute of the context manager corresponding to the name of the
annotation type.

The primary function for queries is :code:`filter`. This function takes one or more
conditional expressions on attributes of annotations.  In the above example,
:code:`word` annotations have an attribute :code:`label` which corresponds to the
orthography.

Conditional expressions can take on any normal Python conditional (:code:`==`,
:code:`!=`, :code:`<`, :code:`<=`, :code:`>`, :code:`>=`).  The Python
operator :code:`in` does not work; a special pattern has to be used:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       print(q.all())

The :code:`in_` conditional function can take any iterable, including another query:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       sub_q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       q = c.query_graph(c.phone).filter(c.word.id.in_(sub_q))
       print(q.all())

In this case, it will find all :code:`phone` annotations that are in the words
listed.  Using the :code:`id` attribute will use unique identifiers for the filter.
In this particular instance, it does not matter, but it does in the following:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       sub_q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       sub_q = sub_q.filter_right_aligned(c.line)
       q = c.query_graph(c.phone).filter(c.word.id.in_(sub_q))
       print(q.all())


The above query will find all instances of the three words, but only where
they are right-aligned with a :code:`line` annotation.

.. note:: Queries are lazy evaluated.  In the above example, :code:`sub_q` is
   not evaluated until :code:`q.all()` is called.  This means that filters
   can be chained across multiple lines without a performance hit.

Specialized filters
-------------------

In addition to :code:`filter`, there are several specialized filter functions
that refer to other types of annotation.  The :code:`filter_right_aligned` was
shown above.  The full list is:

* filter_left_aligned
* filter_right_aligned
* filter_contains
* filter_contained_by

The alignment filters check whether right edges or the left edges of both
annotation types are aligned.  The containment filters refer explicitly to
hierarchical structure.  The :code:`filter_contains` checks whether the higher
annotation contains a lower annotation that matches the criteria:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       q = q.filter_contains(c.phone.label == 'aa')
       print(q.all())


In this example, it will find all instances of the three words that contain
an 'aa' phone.

The :code:`filter_contained_by` function does the opposite, checking whether
the annotation is contained by an annotation that matches a condition:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter_contains(c.word.label.in_(['are', 'is','am']))
       print(q.all())

The above example finds a similar set of labels as the one above that,
but the returned annotation types are different.


.. _following_previous:

Following and previous annotations
----------------------------------

Filters can reference the surrounding local context.  For instance:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')
       print(q.all())


The above query will find all the 'aa' phones that are followed by an 'r'
phone.  Similarly, :code:`c.phone.previous` would provide access to filtering on
preceding phones.

.. _aggregates_and_groups:

Aggregates and groups
=====================

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
       print(q.aggregate(Count()))


Like the :code:`all` function, :code:`aggregate` triggers evaluation of the query.
Instead of returning rows, it will return a single number, which is the
number of rows matching this query.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')
       print(q.aggregate(Average(c.phone.duration)))


The above aggregate function will return the average duration for all 'aa'
phones followed by 'r' phones.

Aggregates are particularly useful with grouping.  For instance:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label.in_(['r','l']))
       q = q.group_by(c.phone.following.label.column_name('following_label'))
       print(q.aggregate(Average(c.phone.duration), Count()))


The above query will return the average duration and the count of 'aa'
phones grouped by whether they're followed by an 'r' or an 'l'.

.. note:: In the above example, the :code:`group_by` attribute is supplied with
   an alias for output.  In the print statment and in the results, the column
   will be called 'following_label' instead of the default (more opaque) one.

.. _ordering:

Ordering
========

The :code:`order_by` function is used to provide an ordering to the results of
a query.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label.in_(['r','l']))
       q = q.filter(c.phone.discourse == 'a_discourse')
       q = q.order_by(c.phone.begin)
       print(q.all())


The results for the above query will be ordered by the timepoint of the
annotation.  Ordering by time is most useful for when looking at single
discourses (as including multiple discourses in a query would invalidate the
ordering).

.. note:: In grouped aggregate queries, ordering is by default by the
   first :code:`group_by` attribute.  This can be changed by calling :code:`order_by`
   before evaluating with :code:`aggregate`.
