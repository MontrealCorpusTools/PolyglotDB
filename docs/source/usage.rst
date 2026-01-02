
.. _SPADE analysis repository: https://github.com/MontrealCorpusTools/SPADE

.. _admin section of the ISCAN server: https://iscan.readthedocs.io/en/latest/administration.html

.. _basic_queries.py: https://github.com/MontrealCorpusTools/SPADE/blob/master/basic_queries.py

.. _local:

Interacting with a local Polyglot database
==========================================

There are two potential ways to have a local Polyglot instance up and running on your local machine.  The first is a
command line utility :code:`pgdb`.  The other option is to connect to
a locally running ISCAN server instance.


pgdb utility
------------

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

Once :code:`pgdb start` has executed, the local Neo4j instance can be seen at :code:`http://localhost:7474/`.

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


These port settings are used by default and so connecting to a vanilla install of the ``pgdb`` utility can be done more simply
through the following:

.. code-block:: python

    from polyglotdb import CorpusContext

    with CorpusContext('corpus_name') as c:
        pass # replace with some task, i.e., import, enrichment, or query


See the tutorial scripts for examples that use this style of connecting to a local ``pgdb`` instance.

.. _local_iscan_server:

Local ISCAN server
------------------

A locally running ISCAN server is a more fully functional system that can manage multiple Polyglot databases (creating, starting and stopping
as necessary through a graphical web interface).
While ISCAN servers are intended to be run on dedicated remote servers, there will often be times where scripts
will need to connect a locally running server.  For this, there is a utility function :code:`ensure_local_database_running`:

.. code-block:: python

    from polyglotdb import CorpusContext, CorpusConfig
    from polyglotdb.utils import ensure_local_database_running

    with ensure_local_database_running('database', port=8080, token='auth_token_from_iscan') as connection_params:
        config = CorpusConfig('corpus_name', **connection_params)
        with CorpusContext(config) as c:
            pass # replace with some task, i.e., import, enrichment, or query

.. important::

   Replace the ``database``, ``auth_token_from_iscan``, and ``corpus_name`` with relevant values.  In the use case of one
   corpus per database,
   ``database`` and ``corpus_name`` can be the same name, as in the `SPADE analysis repository`_.

As compared to the example above, the only difference is the context manager use of :code:`ensure_local_database_running`.
What this function does is first try to connect to a ISCAN server running on the local machine.
If it successfully connects, then it creates a new database named :code:`"database"` if it does not already exist, starts it if
it is not already running, and then returns the connection parameters as a dictionary that can be used for instantiating
the :code:`CorpusConfig` object.  Once all the work inside the context of :code:`ensure_local_database_running` has been completed, the
database will be stopped.

The token keyword argument should be an authentication token for a user with appropriate permissions to access the ISCAN
server.  This token can be found by going to the admin page for tokens within ISCAN (by default, http://localhost:8080/admin/auth_token/)
and choosing an appropriate one.  However, please ensure that this token is not committed or made public in any way as
that would lead to security issues.  One way to use this in committed code is to have the token saved in a separate text
document that git does not track, and load it via a function like:

.. code-block:: python

    def load_token():
        token_path = os.path.join(base_dir, 'auth_token')
        if not os.path.exists(token_path):
            return None
        with open(token_path, 'r') as f:
            token = f.read().strip()
        return token

.. note::

   The ISCAN server keeps track of all existing databases and ensures that the ports do not overlap, so multiple databases
   can be run simultaneously.  The ports are all in the 7400 and 8400 range, and should not (but may) conflict with other applications.

This utility is thus best for isolated work by a single user, where only they will be interacting
with the particular database specified and the database only needs to be available during the running of the script.

You can see an example of connecting to local ISCAN server used in the scripts for the `SPADE analysis repository`_,
for instance the `basic_queries.py`_ script.
