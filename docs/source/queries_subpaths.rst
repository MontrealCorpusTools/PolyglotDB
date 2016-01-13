

.. _subpaths:


********************
Hierarchical queries
********************

A key facet of language is that it is hierarchical.  Words contain phones,
and can be contained in larger utterances.  There are several ways to
query hierarchical information.  If we want to find all "aa" phones in the
word "dogs", then we can perform the following query:


.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
       q = q.filter_contained_by(g.word.label == 'dogs')

       results = q.all()
       print(results)

The ``filter`` function can also be used for implicit containment queries:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
       q = q.filter(g.word.label == 'dogs')

       results = q.all()
       print(results)

Starting from the word level, we might want to know what phones each word
contains.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = g.query_graph(g.word)
       q = q.columns(g.word.phone.label.column('phones'))

       results = q.all()
       print(results)

In the output of the above query, there would be a column labeled "phones"
that contains a list of the labels of phones that belong to the word
(``['d', 'aa', 'g', 'z']``). Any property of phones can be queried this
way (i.e., 'begin', 'end', 'duration', etc).

Special keywords exist for these containment columns. The keyword 'rate'
will return the elements per second for the word (i.e., phones per second).
The keyword 'count' will return the number of elements.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = g.query_graph(g.word)
       q = q.columns(g.word.phone.rate.column('phones_per_second'))
       q = q.columns(g.word.phone.count.column('num_phones'))

       results = q.all()
       print(results)

Additionally, there is a special keyword can be used to query the position
of a contained element in a containing one.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
       q = q.filter(g.word.label == 'dogs')
       q = q.columns(g.word.phone.position.column_name('position_in_word'))

       results = q.all()
       print(results)

The above query should return ``2`` for the value of 'position_in_word',
as the "aa" phone would be the second phone.
