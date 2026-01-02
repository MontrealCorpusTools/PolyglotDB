
.. _export:

***********************
Exporting query results
***********************

Exporting queries is simply a matter of calling the ``to_csv`` function of a query, rather than its ``all`` function.

.. code-block:: python

   csv_path = '/path/to/save/file.csv'
   with CorpusContext(config) as c:
       q = c.query_graph(c.word).filter(c.word.label == 'are')
       q = q.columns(c.word.label.column_name('word'), c.word.duration,
                     c.word.speaker.name.column_name('speaker'))
       q.to_csv(csv_path)


All queries, including those over annotations, speakers, discourses, etc, have this method available for creating CSV files from
their results.  The ``columns`` function allows for users to list any attributes within the query, (i.e., properties of the
word, or any higher/previous/following annotation, or anything about the speaker, etc).  These attributes by default have
a column header generated based on the query, but these headers can be overwritten through the use of the ``column_name``
function, as above.

.. _export_tokens:

Export for token CSVs
---------------------

If you wish to add properties to a set of tokens by means of a CSV, this can be achieved by using the token import tool explained in :ref:`enrich_tokens`.
In order do this you will need a CSV that contains the ID of each token that you wish to evaluate.
The following code shows how to export all phones with their ID, begin, end and sound file, which could be useful for a phonetic analysis in an external tool.

.. code-block:: python

   csv_path = '/path/to/save/file.csv'
   with CorpusContext(config) as c:
       q = c.query_graph(c.phone)
       q = q.columns(c.phone.label, \
                     c.phone.id, \
                     c.phone.begin, \
                     c.phone.end, \
                     c.phone.discourse.name)
       q = q.order_by(g.phone.begin)
       q.to_csv(csv_path)
