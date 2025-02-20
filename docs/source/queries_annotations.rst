

.. _annotation_queries:

********************
Querying annotations
********************

The main way of finding specific annotations is through the :code:`query_graph` method of
:code:`CorpusContext` objects.

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.word).filter(c.word.label == 'are')
       results = q.all()
       print(results)

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

   with CorpusContext(config) as c:
       q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       results = q.all()
       print(results)

The :code:`in_` conditional function can take any iterable, including another query:

.. code-block:: python

   with CorpusContext(config) as c:
       sub_q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       q = c.query_graph(c.phone).filter(c.phone.word.id.in_(sub_q))
       results = q.all()
       print(results)

In this case, it will find all :code:`phone` annotations that are in the words
listed.  Using the :code:`id` attribute will use unique identifiers for the filter.
In this particular instance, it does not matter, but it does in the following:

.. code-block:: python

   with CorpusContext(config) as c:
       sub_q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       sub_q = sub_q.filter_right_aligned(c.word.line)
       q = c.query_graph(c.phone).filter(c.phone.word.id.in_(sub_q))
       results = q.all()
       print(results)


The above query will find all instances of the three words, but only where
they are right-aligned with a :code:`line` annotation.

.. note:: Queries are lazy evaluated.  In the above example, :code:`sub_q` is
   not evaluated until :code:`q.all()` is called.  This means that filters
   can be chained across multiple lines without a performance hit.

.. _following_previous:

Following and previous annotations
----------------------------------

Filters can reference the surrounding local context.  For instance:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')
       results = q.all()
       print(results)


The above query will find all the 'aa' phones that are followed by an 'r'
phone.  Similarly, :code:`c.phone.previous` would provide access to filtering on
preceding phones.

.. _query_annotation_subset:

Subsetting annotations
----------------------

In linguistics, it's often useful to specify subsets of symbols as particular classes.
For instance, phonemes are grouped together by whether they are syllabic,
their manner/place of articulation, and vowel height/backness/rounding, and
words are grouped by their parts of speech.


Suppose a subset has been created as in :ref:`enrichment_subsets`, so that the phones 'aa' and 'ih' have been marked as `syllabic`.
Once this category is encoded in the database, it can be used in filters.

.. code-block:: python

   with CorpusContext('corpus') as c:
       q = c.query_graph(c.phone)
       q = q.filter(c.phone.subset=='syllabic')
       results = q.all()
       print(results)

.. note::

   The results returned by the above query will be identical to the similar query:

   .. code-block:: python

       with CorpusContext('corpus') as c:
           q = c.query_graph(c.phone)
           q = q.filter(c.phone.label.in_(['aa', 'ih']))
           results = q.all()
           print(results)

   The primary benefits of using subsets are performance based due to the inner workings of Neo4j.  See :ref:`neo4j_implementation`
   for more details.

Another way to specify subsets is on the phone annotations themselves, as follows:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone.filter_by_subset('syllabic'))
       results = q.all()
       print(results)

Both of these queries are identical and will return all instances of 'aa' and 'ih' phones.  The benefit of `filter_by_subset`
is generally for use in :ref:`hierarchical_queries`.

.. note:: Using repeated subsets repeatedly in queries can make them overly
   verbose.  The objects that the queries use are normal Python objects
   and can therefore be assigned to variables for easier use.

   .. code-block:: python

      with CorpusContext(config) as c:
          syl = c.phone.filter_by_subset('syllabic')
          q = c.query_graph(syl)
          q = q.filter(syl.end == syl.word.end)
          results = q.all()
          print(results)

    The above query would find all phones marked by '+syllabic' that are
    at the ends of words.


.. _hierarchical_queries:

Hierarchical queries
--------------------

A key facet of language is that it is hierarchical.  Words contain phones,
and can be contained in larger utterances.  There are several ways to
query hierarchical information.  If we want to find all ``aa`` phones in the
word ``dogs``, then we can perform the following query:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.word.label == 'dogs')
       results = q.all()
       print(results)

Starting from the word level, we might want to know what phones each word
contains.

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.word)
       q = q.columns(c.word.phone.label.column_name('phones'))
       results = q.all()
       print(results)

In the output of the above query, there would be a column labeled ``phones``
that contains a list of the labels of phones that belong to the word
(``['d', 'aa', 'g', 'z']``). Any property of phones can be queried this
way (i.e., ``begin``, ``end``, ``duration``, etc).

Going down the hierarchy, we can also find all words that contain a certain phone.

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.word).filter(c.word.label.in_(['are', 'is','am']))
       q = q.filter(c.word.phone.label == 'aa')
       results = q.all()
       print(results)


In this example, it will find all instances of the three words that contain
an ``aa`` phone.

Special keywords exist for these containment columns. The keyword ``rate``
will return the elements per second for the word (i.e., phones per second).
The keyword ``count`` will return the number of elements.

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.word)
       q = q.columns(c.word.phone.rate.column_name('phones_per_second'))
       q = q.columns(c.word.phone.count.column_name('num_phones'))
       results = q.all()
       print(results)

These keywords can also leverage subsets, as above:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.word)
       q = q.columns(c.word.phone.rate.column_name('phones_per_second'))
       q = q.columns(c.word.phone.filter_by_subset('+syllabic').count.column_name('num_syllabic_phones'))
       q = q.columns(c.word.phone.count.column_name('num_phones'))
       results = q.all()
       print(results)

Additionally, there is a special keyword can be used to query the ``position``
of a contained element in a containing one.

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.word.label == 'dogs')
       q = q.columns(c.word.phone.position.column_name('position_in_word'))
       results = q.all()
       print(results)

The above query should return ``2`` for the value of ``position_in_word``,
as the ``aa`` phone would be the second phone.


.. _queries_subannotations:

Subannotation queries
---------------------

Annotations can have subannotations associated with them.  Subannotations
are not independent linguistic types, but have more information associated
with them than just a single property.  For instance, voice onset time (VOT)
would be a subannotation of stops (as it has a begin time and an end time
that are of interest).
For mor information on subannotations, see :ref:`enrichment_subannotations`.
Querying such subannotations would be performed as follows:


.. code-block:: python

   with CorpusContext(config) as c:
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

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q = q.columns(c.phone.voicing_during_closure.duration.column_name('voicing'))
       results = q.all()
       print(results)

In some cases, we might like to know the total duration of such subannotations,
rather than the individual durations.  To query that information, we can
use an ``aggregate``:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       results = q.aggregate(Sum(c.phone.voicing_during_closure.duration).column_name('total_voicing'))
       print(results)


Miscellaneous
=============

.. _aggregates_and_groups:

Aggregates and groups
---------------------

Aggregate functions are available in :code:`polyglotdb.query.base.func`.  Aggregate
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

   from polyglotdb.query.base.func import Count
   with CorpusContext(config) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')
       result = q.aggregate(Count())
       print(result)


Like the :code:`all` function, :code:`aggregate` triggers evaluation of the query.
Instead of returning rows, it will return a single number, which is the
number of rows matching this query.

.. code-block:: python

   from polyglotdb.query.base.func import Average
   with CorpusContext(config) as c:
       q = c.query_graph(c.phone).filter(c.phone.label == 'aa')
       q = q.filter(c.phone.following.label == 'r')
       result = q.aggregate(Average(c.phone.duration))
       print(result)


The above aggregate function will return the average duration for all 'aa'
phones followed by 'r' phones.

Aggregates are particularly useful with grouping.  For instance:

.. code-block:: python

   from polyglotdb.query.base.func import Average
   with CorpusContext(config) as c:
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

.. _ordering:

Ordering
--------

The :code:`order_by` function is used to provide an ordering to the results of
a query.

.. code-block:: python

   with CorpusContext(config) as c:
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
