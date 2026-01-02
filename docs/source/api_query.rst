.. _graph_api:

*********
Query API
*********

.. _base_queries_api:

Base
====

.. currentmodule:: polyglotdb.query.base.query

.. autosummary::
   :toctree: generated/
   :template: class.rst

   BaseQuery

.. _base_attributes_api:

Attributes
----------
.. currentmodule:: polyglotdb.query.annotations.attributes.base

.. autosummary::
   :toctree: generated/
   :template: class.rst

   Node
   NodeAttribute
   CollectionNode
   CollectionAttribute

.. _base_clauses_api:

Clause elements
---------------
.. currentmodule:: polyglotdb.query.annotations.elements

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

.. _base_aggregates_api:

Aggregate functions
-------------------
.. currentmodule:: polyglotdb.query.base.func

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

.. _annotation_queries_api:

Annotation queries
==================

.. currentmodule:: polyglotdb.query.annotations.query

.. autosummary::
   :toctree: generated/
   :template: class.rst

   GraphQuery
   SplitQuery

.. _annotation_attributes_api:

Attributes
----------
.. currentmodule:: polyglotdb.query.annotations.attributes.base

.. autosummary::
   :toctree: generated/
   :template: class.rst

   AnnotationNode
   AnnotationAttribute

.. _annotation_clauses_api:

Clause elements
---------------
.. currentmodule:: polyglotdb.query.annotations.elements

.. autosummary::
   :toctree: generated/
   :template: class.rst

   ContainsClauseElement


.. _lexicon_queries_api:

Lexicon queries
===============

.. currentmodule:: polyglotdb.query.lexicon.query

.. autosummary::
   :toctree: generated/
   :template: class.rst

   LexiconQuery


.. _speaker_queries_api:

Speaker queries
===============

.. currentmodule:: polyglotdb.query.speaker.query

.. autosummary::
   :toctree: generated/
   :template: class.rst

   SpeakerQuery


.. _speaker_attributes_api:

Attributes
----------
.. currentmodule:: polyglotdb.query.speaker.attributes

.. autosummary::
   :toctree: generated/
   :template: class.rst

   SpeakerNode
   SpeakerAttribute
   DiscourseNode
   DiscourseCollectionNode
   ChannelAttribute


.. _discourse_queries_api:

Discourse queries
=================

.. currentmodule:: polyglotdb.query.discourse.query

.. autosummary::
   :toctree: generated/
   :template: class.rst

   DiscourseQuery


.. _discourse_attributes_api:

Attributes
----------
.. currentmodule:: polyglotdb.query.discourse.attributes

.. autosummary::
   :toctree: generated/
   :template: class.rst

   DiscourseNode
   DiscourseAttribute
   SpeakerNode
   SpeakerCollectionNode
   ChannelAttribute
