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
#. Install PolyglotDB via :code:`python setup.py install`

