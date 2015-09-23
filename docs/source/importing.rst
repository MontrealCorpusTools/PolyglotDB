.. _importing:

*****************
Importing corpora
*****************


Corpora can be imported from several input formats.  The list of currently
supported formats is:


* Praat TextGrids
* Interlinear gloss text
* Plain running text
* CSV (no annotation graphs are made)
* TIMIT
* Buckeye

To import a corpus, the :code:`CorpusContext` context manager has to be imported
from :code:`polyglotdb`:

.. code-block:: python

   from polyglotdb.corpus import CorpusContext

:code:`CorpusContext` is the primary way through which corpora can be interacted
with.

Before importing a corpus, you should ensure that a Neo4j server is running.
Interacting with corpora requires submitting the connection details.  The
easiest way to do this is to store them in a dictionary:

.. code-block:: python

   graph_db_login = {'host':'localhost', 'port': 7474,
                'user': 'neo4j', 'password': 'whateverpasswordyouused'}


To load a corpus (in this case a TextGrid):

.. code-block:: python

   import polyglotdb.io as pgio

   annotation_types = pgio.inspect_discourse_textgrid('/path/to/textgrid.TextGrid')

   with CorpusContext(corpus_name = 'my_corpus', **graph_db_login) as c:
       pgio.load_discourse_textgrid(c, '/path/to/textgrid.TextGrid',
                                        annotation_types)

In the above code, the :code:`io` module is imported and provides access to
all the importing and exporting functions.  For every format, there is an
inspect function to generate annotation types.  In the case of a TextGrid,
the annotation types correspond to interval tiers.  The inspect function
tries to guess the relevant attributes of each tier.  For instance, if a
TextGrid has a tier 'Words' and a tier 'Phones', it will identify 'Words'
as containing 'Phones' if the 'Phones' tier has more intervals than the 'Words'
tier.

.. note:: All load functions accept a keyword argument for :code:`annotation_types`
   to allow the user to modify aspects of how a corpus is imported.  For set
   standards, such as the Buckeye corpus, annotation_types do not have to be
   explicitly loaded.  See :code:`examples/buckeye_loading.py` in the Git repository
   for an example of loading the complete Buckeye corpus.

All interaction with the databases is via the :code:`CorpusContext` context manager.
The alias for the context manager (:code:`c` above) is passed to the import functions
as the first argument.  Further details on import arguments can be found
in the API documentation.

Once the above code is run, corpora can be queried and explored.
