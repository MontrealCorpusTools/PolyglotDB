.. _enrichment_hierarchical:

***********************
Hierarchical enrichment
***********************

Hierarchical enrichment is for encoding properties that reference multiple levels of annotations.  For instance, something
like speech rate of an utterance requires referencing both utterances as well as the rate per second of an annotation type
below, usually syllables.  Likewise, encoding number of syllables in a word or the position of a phone in a word again
reference multiple levels of annotation.

.. note::

   See :ref:`dev_annotation_graphs` for details on the implementation and representations of the annotation graph hierarchy
   that PolyglotDB uses.

.. _enrichment_count:

Encode count
============

Count enrichment creates a property on the higher annotation that is a measure of the number of lower annotations of a type it
contains.  For instance, if we want to encode how many phones there are within each word, the following code is used:

.. code-block:: python

    with CorpusContext('corpus') as c:
        c.encode_count('word', 'phone', 'number_of_phones')

Following enrichment, all word tokens will have a property for ``number_of_phones`` that can be referenced in queries
and exports.


.. _enrichment_rate:

Encode rate
===========

Rate enrichment creates a property on a `higher` annotation that is a measure of lower annotations per second.  It is calculated
as the count of units contained by the higher annotation divided by the duration of the higher annotation.

.. code-block:: python

    with CorpusContext('corpus') as c:
        c.encode_rate('word', 'phone', 'phones_per_second')

Following enrichment, all word tokens will have a property for ``phones_per_second`` that can be referenced in queries
and exports.

.. _enrichment_position:

Encode position
===============

Position enrichment creates a property on the `lower` annotation that is the position of the element in relation to other
annotations within a higher annotation.  It starts at 1 for the first element.

.. code-block:: python

    with CorpusContext('corpus') as c:
        c.encode_position('word', 'phone', 'position_in_word')

The encoded property is then queryable/exportable, as follows:

.. code-block:: python

   with CorpusContext('corpus') as c:
        q = c.query_graph(c.phone).filter(c.phone.position_in_word == 1)
        print(q.all())

The above query will match all phones in the first position (i.e., identical results to a query using alignment, see
:ref:`hierarchical_queries` for more details on those).
