
.. _Montreal Forced Aligner: https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner

.. _FAVE-align: https://github.com/JoFrhwld/FAVE

.. _LaBB-CAT: http://labbcat.sourceforge.net/

.. _TIMIT: https://catalog.ldc.upenn.edu/LDC93S1

.. _Buckeye: https://buckeyecorpus.osu.edu/

.. _BAS Partitur: http://www.bas.uni-muenchen.de/forschung/publikationen/Granada-98-Partitur.pdf


.. _importing:

*****************
Importing corpora
*****************


Corpora can be imported from several input formats.  The list of currently
supported formats is:


* TextGrids from `Montreal Forced Aligner`_ or `FAVE-align`_
* Praat TextGrids
* TextGrids exported from `LaBB-CAT`_
* `BAS Partitur`_ format
* `TIMIT`_
* `Buckeye`_

Each format has a inspection function in the :code:`polyglot.io` submodule that will check that format of the specified directory
or file matches the input format and return the appropriate parser.

These functions would be used as follows:

.. code-block:: python

   import polyglotdb.io as pgio

   corpus_directory = '/path/to/directory'

   parser = pgio.inspect_mfa(corpus_directory) # MFA output TextGrids

   # OR

   parser = pgio.inspect_fave(corpus_directory) # FAVE output TextGrids

   # OR

   parser = pgio.inspect_textgrid(corpus_directory)

   # OR

   parser = pgio.inspect_labbcat(corpus_directory)

   # OR

   parser = pgio.inspect_partitur(corpus_directory)

   # OR

   parser = pgio.inspect_timit(corpus_directory)

   # OR

   parser = pgio.inspect_buckeye(corpus_directory)



.. note::

   For more technical detail on the inspect functions and the parser objects they return, see :ref:`pgdb_io`.

To import a corpus, the :code:`CorpusContext` context manager has to be imported
from :code:`polyglotdb`:

.. code-block:: python

   from polyglotdb import CorpusContext

:code:`CorpusContext` is the primary way through which corpora can be interacted
with.

Before importing a corpus, you should ensure that a Neo4j server is running.
Interacting with corpora requires submitting the connection details.  The
easiest way to do this is with a utility function :code:`ensure_local_database_running` (see :ref:`local` for more
information):

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
   which the user can modify to change how a corpus is imported.  For most standard formats, including TextGrids from
   aligners, no modification is necessary.

All interaction with the databases is via the :code:`CorpusContext` context manager.
Further details on import arguments can be found
in the API documentation.

Once the above code is run, corpora can be queried and explored.
