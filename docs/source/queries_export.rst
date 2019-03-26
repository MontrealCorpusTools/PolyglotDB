
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