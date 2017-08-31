.. _enrichment_csvs:

************************
Enrichment via CSV files
************************

PolyglotDB supports ways of adding arbitrary information to annotations or metadata about speakers and files by specifying
a local CSV file to add information from.  When constructing this CSV file, the first column should be the label used to
identify which element should be enriched, and all subsequent columns are used as properties to add to the corpus.

::

   ID_column,property_one,property_two
   first_item,first_item_value_one,first_item_value_two
   second_item,,second_item_value_two

Enriching using this file would look up elements based on the `ID_column`, and the one matching `first_item` would get
both `property_one` and `property_two` (with the respective values).  The one matching `second_item` would only get a
`property_two` (because the value for `property_one` is empty.

.. _enrich_lexicon:

Enriching the lexicon
=====================

.. code-block:: python

   lexicon_csv_path = '/full/path/to/lexicon/data.csv'
   with CorpusContext(config) as c:
       c.enrich_lexicon_from_csv(lexicon_csv_path)


.. note::

   The function `enrich_lexicon_from_csv` accepts an optional keyword `case_sensitive` and defaults to `False`.  Changing this
   will respect capitalization when looking up words.


.. _enrich_inventory:

Enriching the phonological inventory
====================================

The phone inventory can be enriched with arbitrary properties via:

.. code-block:: python

   inventory_csv_path = '/full/path/to/inventory/data.csv'
   with CorpusContext(config) as c:
       c.enrich_inventory_from_csv(inventory_csv_path)

.. _enrich_speakers:

Enriching speaker information
=============================

Speaker information can be added via:

.. code-block:: python

   speaker_csv_path = '/full/path/to/speaker/data.csv'
   with CorpusContext(config) as c:
       c.enrich_speakers_from_csv(speaker_csv_path)

.. _enrich_discourses:

Enriching discourse information
===============================

Metadata about the discourses or sound files can be added via:

.. code-block:: python

   discourse_csv_path = '/full/path/to/discourse/data.csv'
   with CorpusContext(config) as c:
       c.enrich_discourses_from_csv(discourse_csv_path)
