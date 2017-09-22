
.. _local:

Interacting with a local Polyglot instance
==========================================

There are two potential ways to have a local Polyglot instance up and running on your local machine.  The first is a
command line utility :code:`pgdb.py` that is in the :code:`bin` folder of the Git repository.  The other option is to connect to
a locally running polyglot server instance.


pgdb.py utility
---------------

This utility provides a basic way to install/start/stop all of the required databases in a Polyglot database (see
:ref:`local_setup` for more details on setting up a Polyglot instance this way).

When using this set up the following ports are used (and are relevant for later connecting with the corpus):

+-------+----------+----------+
|  Port | Protocol | Database |
+=======+==========+==========+
| 7474  | HTTP     | Neo4j    |
+-------+----------+----------+
| 7475  | HTTPS    | Neo4j    |
+-------+----------+----------+
| 7687  | Bolt     | Neo4j    |
+-------+----------+----------+
| 8086  | HTTP     | InfluxDB |
+-------+----------+----------+
| 8087  | UDP      | InfluxDB |
+-------+----------+----------+

If any of those ports are in use by other programs (they're also the default ports for the respective database software),
then the Polyglot instance will not be able to start.

Once :code:`pgdb.py start` has executed, the local Neo4j instance can be seen at :code:`http://localhost:7474/`

Connecting from a script
````````````````````````

When the Polyglot instance is running locally, scripts can connect to the relevant databases through the use of parameters passed to
CorpusContext objects (or CorpusConfig objects):


.. code-block:: python

    from polyglotdb import CorpusContext, CorpusConfig

    connection_params = {'host': 'localhost',
                        'graph_http_port': 7474,
                        'graph_bolt_port': 7687,
                        'acoustic_http_port': 8086}
    config = CorpusConfig('corpus_name', **connection_params)
    with CorpusContext(config) as c:
        pass # replace with some task, i.e., import, enrichment, or query


The utility function :code:`ensure_local_database_running` will return the above parameters if it does not detect a Polyglot server
running, so the code below will work as well (the database name is ignored because only one database can be run through the
:code:`pgdb.py` utility script.

.. _local_polyglot_server:

Local Polyglot server
---------------------

A local Polyglot server is a more fully functional system that can manage multiple Polyglot databases (creating, starting and stopping
as necessary).  While Polyglot servers are intended to be run on dedicated servers, there will often be times where scripts
will need to connect a locally running server.  For this, there is a utility function :code:`ensure_local_database_running`:

.. code-block:: python

    from polyglotdb import CorpusContext, CorpusConfig
    from polyglotdb.utils import ensure_local_database_running

    with ensure_local_database_running('database') as connection_params:
        config = CorpusConfig('corpus_name', **connection_params)
        with CorpusContext(config) as c:
            pass # replace with some task, i.e., import, enrichment, or query

As compared to the example above, the only difference is the context manager use of :code:`ensure_local_database_running`.
What this function does is first try to connect to a Polyglot server running on the local machine.
If it successfully connects, then it creates a new database named :code:`"database"` if it does not already exist, start it if
it is not already running, and then return the connection parameters as a dictionary that can be used for instantiating
the CorpusConfig object.  Once all the work inside the context of :code:`ensure_local_database_running` has been completed, the
database will be stopped.

.. note::

   The Polyglot server keeps track of all existing databases and ensures that the ports do not overlap, so multiple databases
   can be run simultaneously.  The ports are all in the 7400 and 8400 range, but should not (but may) conflict with other applications.

This utility is thus best for isolated work by a single user, where only they will be interacting
with the particular database specified and the database only needs to be available during the running of the script.
In cases where there are multiple users, or longer up times are needed, then the server should be interacted with through a
client object.

You can see an example of this type of script in the :code:`examples/formant_analysis/refined_formants_example.py` script.