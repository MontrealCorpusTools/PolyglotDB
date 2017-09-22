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

   from polyglotdb import CorpusContext

:code:`CorpusContext` is the primary way through which corpora can be interacted
with.

Before importing a corpus, you should ensure that a Neo4j server is running.
Interacting with corpora requires submitting the connection details.  The
easiest way to do this is with a utility function :code:`ensure_local_database_running`:

.. code-block:: python

   from polyglotdb.utils import ensure_local_database_running
   from polyglotdb import CorpusConfig

   with ensure_local_database_running('database_name') as connection_params:
      config = CorpusConfig('corpus_name', **connection_params)


The above :code:`config` object contains all the configuration for the corpus.

To import a file into a corpus (in this case a TextGrid):

.. code-block:: python

   import polyglotdb.io as pgio

   parser = pgio.inspect_textgrid('/path/to/textgrid.TextGrid')

   with ensure_local_database_running('database_name') as connection_params:
      config = CorpusConfig('my_corpus', **connection_params)
      with CorpusContext(config) as c:
          c.load(parser, '/path/to/textgrid.TextGrid')

In the above code, the :code:`io` module is imported and provides access to
all the importing and exporting functions.  For every format, there is an
inspect function to generate a parser for that file and other ones that are
formatted the same.  In the case of a TextGrid,
the parser has annotation types correspond to interval and point tiers.
The inspect function
tries to guess the relevant attributes of each tier.

.. note::

   The discourse load function of :code:`Corpuscontext` objects takes
   a parser as the first argument. Parsers contain an attribute :code:`annotation_types`,
   which the user can modify to change how a corpus is imported.

All interaction with the databases is via the :code:`CorpusContext` context manager.
Further details on import arguments can be found
in the API documentation.

Once the above code is run, corpora can be queried and explored.
