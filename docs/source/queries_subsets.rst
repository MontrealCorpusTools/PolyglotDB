
.. _subsetting:


**********************
Subsetting annotations
**********************

In linguistics, it's often useful to specify subsets of symbols as particular classes.
For instance, phonemes are grouped together by whether they are syllabic,
their manner/place of articulation, and vowel height/backness/rounding, and
words are grouped by their parts of speech.

In PolyglotDB, creating a subset is as follows:

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone).filter(c.phone.label.in_(['aa', 'ih']))
       q.set_type('+syllabic')

After running that code, the phones 'aa' and 'ih' would be marked in the database
as '+syllabic'.  The string for the category can contain any characters.
Once this category is encoded in the database, queries can be run just on
those subsets.

.. code-block:: python

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       q = c.query_graph(c.phone.subset('+syllabic'))

       results = q.all()
       print(results)

The above query will return all instances of 'aa' and 'ih' phones.

.. note:: Using repeated subsets repeatedly in queries can make them overly
   verbose.  The objects that the queries use are normal Python objects
   and can therefore be assigned to variables for easier use.

   .. code-block:: python

      with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
          syl = c.phone.subset('+syllabic')
          q = c.query_graph(syl)
          q = q.filter(syl.end == c.word.end)

          results = q.all()
          print(results)

    The above query would find all phones marked by '+syllabic' that are
    at the ends of words.
