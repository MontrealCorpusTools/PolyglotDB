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

Enriching using this file would look up elements based on the ``ID_column``, and the one matching ``first_item`` would get
both ``property_one`` and `property_two` (with the respective values).  The one matching ``second_item`` would only get a
``property_two`` (because the value for ``property_one`` is empty.

.. _enrich_lexicon:

Enriching the lexicon
=====================

.. code-block:: python

   lexicon_csv_path = '/full/path/to/lexicon/data.csv'
   with CorpusContext(config) as c:
       c.enrich_lexicon_from_csv(lexicon_csv_path)


.. note::

   The function ``enrich_lexicon_from_csv`` accepts an optional keyword ``case_sensitive`` and defaults to ``False``.  Changing this
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


.. _enrich_tokens:

Enriching arbitrary tokens
==========================

Often it's necessary or useful to encode a new property on tokens of an annotation without directly interfacing the database.
This could happen, for example, if you wanted to use a different language or tool for a certain phonetic analysis than Python.
In this case, it is possible to enrich any type of token via CSV.
This can be done using the  :code:`corpus_context.enrich_tokens_with_csv` function.

.. code-block:: python

   token_csv_path = '/full/path/to/discourse/data.csv'
   with CorpusContext(config) as c:
       c.enrich_tokens_from_csv(token_csv_path,
               annotation_type="phone",
               id_column="phone_id"
               properties=["measurement_1", "measurement_2"])

The only requirement for the CSV is that there is a column which contains the IDs of the tokens you wish to update.
You can get these IDs (along with other parameters) by querying the tokens before hand, and exporting a CSV, see :ref:`export_tokens`.
The only columns from the CSV that will be added as token properties, are those which are included in the `properties` parameter.
If this parameter is left as ``None``, then all the columns of the CSV except the ``id_column`` will be included.
