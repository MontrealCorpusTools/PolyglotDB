
.. _usage:

Connecting to a PolyglotDB instance
===================================

There are two routes that can be used in PolyglotDB to import, enrich, and query corpora.  The first, and the one that is
the easiest to set up and maintain is to use the client API in PolyglotDB to connect to a Polyglot server (using the class PGDBClient).
This API allows users to interact with corpora more simply, but in more restricted ways.  This API is under heavy active development.
Please see the section on using the :ref:`client` for more details.

The second API (accessed via CorpusContext) requires that the underlying databases be running on the local machine.  The client API connects to a server
that then uses this API to interact with the data.  This API is faster to develop and test, but most parts of it are
stable.  See ref:`local` for more details.


Contents:

.. toctree::
   :maxdepth: 2

   usage_local.rst
   usage_client.rst
