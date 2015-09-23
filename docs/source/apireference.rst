.. _api_reference:

=============
API Reference
=============

.. _corpus_api:

Corpus class
------------
.. currentmodule:: polyglotdb.corpus

.. autosummary::
   :toctree: generated/
   :template: class.rst

   CorpusContext

.. _graph_api:

Graph classes
=============

Queries
-------
.. currentmodule:: polyglotdb.graph.query

.. autosummary::
   :toctree: generated/
   :template: class.rst

   GraphQuery

Attributes
----------
.. currentmodule:: polyglotdb.graph.attributes

.. autosummary::
   :toctree: generated/
   :template: class.rst

   Attribute
   AnnotationAttribute

Clause elements
---------------
.. currentmodule:: polyglotdb.graph.elements

.. autosummary::
   :toctree: generated/
   :template: class.rst

   ClauseElement
   EqualClauseElement
   GtClauseElement
   GteClauseElement
   LtClauseElement
   LteClauseElement
   NotEqualClauseElement
   InClauseElement
   ContainsClauseElement

Aggregate functions
-------------------
.. currentmodule:: polyglotdb.graph.func

.. autosummary::
   :toctree: generated/
   :template: class.rst

   AggregateFunction
   Average
   Count
   Max
   Min
   Stdev
   Sum

.. _corpus_io_api:

Importing and exporting
=======================

Helper classes
--------------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: class.rst

   helper.Attribute
   helper.BaseAnnotation
   helper.Annotation
   helper.AnnotationType
   helper.DiscourseData

Helper functions
----------------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: function.rst

   helper.inspect_directory
   helper.compile_digraphs
   helper.parse_transcription
   helper.text_to_lines
   helper.find_wav_path


Loading from CSV
----------------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: function.rst

   csv.load_corpus_csv
   csv.load_feature_matrix_csv

Export to CSV
-------------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: function.rst

   csv.export_corpus_csv
   csv.export_feature_matrix_csv

TextGrids
---------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: function.rst

   textgrid.inspect_discourse_textgrid
   textgrid.load_discourse_textgrid
   textgrid.load_directory_textgrid

Running text
------------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: function.rst

   text_spelling.inspect_discourse_spelling
   text_spelling.load_discourse_spelling
   text_spelling.load_directory_spelling
   text_spelling.export_discourse_spelling
   text_transcription.inspect_discourse_transcription
   text_transcription.load_discourse_transcription
   text_transcription.load_directory_transcription
   text_transcription.export_discourse_transcription

Interlinear gloss text
----------------------

.. currentmodule:: polyglotdb.io

.. autosummary::
   :toctree: generated/
   :template: function.rst

   text_ilg.inspect_discourse_ilg
   text_ilg.load_discourse_ilg
   text_ilg.load_directory_ilg
   text_ilg.export_discourse_ilg

Buckeye
-------

.. currentmodule:: polyglotdb.io.standards

.. autosummary::
   :toctree: generated/
   :template: function.rst

   buckeye.inspect_discourse_buckeye
   buckeye.load_discourse_buckeye
   buckeye.load_directory_buckeye

TIMIT
-----

.. currentmodule:: polyglotdb.io.standards

.. autosummary::
   :toctree: generated/
   :template: function.rst

   timit.inspect_discourse_timit
   timit.load_discourse_timit
   timit.load_directory_timit
