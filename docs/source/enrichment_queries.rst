.. _enrichment_queries:

**********************
Enrichment via queries
**********************

Queries have the functionality to set properties and create subsets of elements based on results.

For instance, if you wanted to make word initial phones more easily queryable, you could perform the following:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q = q.filter(c.phone.begin == c.phone.word.begin)
       q.create_subset('word-initial')

Once that code completes, a subsequent query could be made of:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q = q.filter(c.phone.subset == 'word-initial)
       print(q.all()))

Or instead of a subset, a property could be encoded as:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q = q.filter(c.phone.begin == c.phone.word.begin)
       q.set_properties(position='word-initial')

And then this property can be exported as a column in a csv:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q.columns(c.position)
       q.to_csv(some_csv_path)


Lexicon queries can also be used in the same way to create subsets and encode properties that do not vary on a token by token basis.

For instance, a subset for high vowels can be created as follows:

.. code-block:: python

   with CorpusContext(config) as c:
       high_vowels = ['iy', 'ih','uw','uh']
       q = c.query_lexicon(c.lexicon_phone)
       q = q.filter(c.lexicon_phone.label.in_(high_vowels))
       q.create_subset('high_vowel')

Which can then be used to query phone annotations:

.. code-block:: python

   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q = q.filter(c.phone.subset == 'high_vowel')
       print(q.all())
