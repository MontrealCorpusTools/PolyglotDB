.. _installation:

************
Installation
************

.. _prerequisites:

Prerequisites
=============

PolyglotDB is the Python API for interacting with PolyglotDB databases.  The easiest way to set up and interface with
a PolyglotDB database is through setting up a [Polyglot server](https://github.com/MontrealCorpusTools/polyglot-server).
The Polyglot server can be set up on a lab's central server, or you can run it on your local computer as well (though many
of PolyglotDB's algorithms benefit from having more processors and memory available).  Please see the Polyglot server
documentation for more information on setting it up (http://polyglot-server.readthedocs.io/en/latest/getting_started.html).

PolyglotDB provides a lightweight Python client for connecting to remote servers without any external prerequisites
(these are handled by the Polyglot server) besides Python packages.

.. _actual_install:

Installation
============

To install via pip:

```
pip install polyglotdb
```

To install from source (primarily for development):

#. Clone or download the Git repository (https://github.com/MontrealCorpusTools/PolyglotDB).
#. Navigate to the directory via command line and install the dependencies via :code:`pip install -r requirements.txt`
#. Install PolyglotDB via :code:`python setup.py install` followed by :code:`python bin/pgdb.py install /path/to/where/you/want/data/to/be/stored`, or :code:`python bin/pgdb.py install` to save data in the default directory.
#. (If on Windows, you may need to navigate to .pgdb/neo4j/ (where .pgdb is the name of your data storage directory if you renamed it during installation), and then run :code:`bin/neo4j.bat install-service` in order to get neo4j to work properly. If you do this, you'll also need to run :code:`bin/neo4j.bat uninstall-service` before you uninstall.)

Once you have installed PolyglotDB, to start it navigate to the PolyglotDB directory and type :code:`python bin/pgdb.py start`. Likewise, you can close PolyglotDB by running :code:`python bin/pgdb.py stop`. 

To uninstall, navigate to the PolyglotDB directory and type :code:`python bin/pgdb.py uninstall`.