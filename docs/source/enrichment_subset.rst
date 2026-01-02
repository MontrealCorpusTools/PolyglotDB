.. _enrichment_subsets:

*****************
Subset enrichment
*****************

One of the most basic aspects of linguistic analysis is creating functional subsets of linguistic units.  In phonology,
for instance, this would be creating classes like ``syllabic`` or ``coronal``.  For words, this might be classes like
``content`` vs ``functional``, or something more fine-grained like ``noun``, ``adjective``, ``verb``, etc.  At the core of
these analyses is the idea that we treat some subset of linguistic units separately from others.  In PolyglotDB, subsets are
a fairly broad and general concept and can be applied to both linguistic types (i.e., phones or words in a lexicon) or
to tokens (i.e., actual productions in a discourse).

For instance, if we wanted to create a subset of phone types that are syllabic, we can run the following code:

.. code-block:: python

    syllabics = ['aa', 'ih']

    with CorpusContext('corpus') as c:
        c.encode_type_subset('phone', syllabics, 'syllabic')

This type subset can then be used as in :ref:`enrichment_syllables`, or for the queries in :ref:`query_annotation_subset`.

Token subsets can also be created, see :ref:`enrichment_queries`.
