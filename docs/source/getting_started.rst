.. _ISCAN server: https://github.com/MontrealCorpusTools/ISCAN

.. _installation:

***************
Getting started
***************

.. _prerequisites:

Prerequisites
=============

PolyglotDB is the Python API for interacting with PolyglotDB databases.  The easiest way to set up and interface with
a PolyglotDB database is through setting up an `ISCAN server`_.
An Integrated Speech Corpus Analysis (ISCAN) server can be set up on a lab's central server, or you can run it on your
local computer as well (though many
of PolyglotDB's algorithms benefit from having more processors and memory available).  Please see the ISCAN
documentation for more information on setting it up (http://iscan.readthedocs.io/en/latest/getting_started.html).

PolyglotDB provides a lightweight Python client for connecting to remote servers without any external prerequisites
(these are handled by the Polyglot server) besides Python packages.

.. _actual_install:

Installation
============

To install via pip:

``pip install polyglotdb``

To install from source (primarily for development):

#. Clone or download the Git repository (https://github.com/MontrealCorpusTools/PolyglotDB).
#. Navigate to the directory via command line and install the dependencies via :code:`pip install -r requirements.txt`
#. Install PolyglotDB via :code:`python setup.py install`, which will install the ``pgdb`` utility that can be run anywhere
   and manages a local database.

.. note::

   The use of ``sudo`` is not recommended for installation.  Ideally your Python installation should be managed by either
   Anaconda or Homebrew (for Macs).

.. _local_setup:

Set up local database
---------------------

Please be aware that this way to set up a database is not recommended for larger groups.  See the `ISCAN server`_ for a more fully featured
solution.

If you do not have access to an ISCAN server, or just want a lightweight version of the server instead, you can use a utility script
that is installed with the PolyglotDB package.

Mac
```

#. Ensure Java 8 is installed inside Anaconda distribution (``conda install -c anaconda openjdk``) if using Anaconda, or
   via Homebrew otherwise (``brew cask install java``)
#. Once PolyglotDB is installed, run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

.. warning::

   Do not use ``sudo`` with this command on Macs, as it will lead to permissions issues later on.

Once you have installed PolyglotDB, to start it run :code:`pgdb start`.
Likewise, you can close PolyglotDB by running :code:`pgdb stop`.

To uninstall, run :code:`pgdb uninstall`

Windows
```````

#. Ensure Java is installed (https://www.java.com/) and on the path (``java --version`` works in the command prompt)
#. Start an Administrator command prompt (right click on cmd.exe and select "Run as administrator"), as Neo4j will be installed as a Windows service.
#. Run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

To start the database, you likewise have to use an administrator command prompt before entering the commands :code:`pgdb start`
or :code:`pgdb stop`.

To uninstall, run :code:`pgdb uninstall` (also requires an administrator command prompt).

Linux
`````

Ensure Java 8 is installed. On Ubuntu:

.. code-block:: bash

   sudo add-apt-repository ppa:webupd8team/java
   sudo apt-get update
   sudo apt-get install oracle-java8-installer

Once installed, run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
:code:`pgdb install` to save data in the default directory.

Once you have installed PolyglotDB, to start it run :code:`pgdb start`.
Likewise, you can close PolyglotDB by running :code:`pgdb stop`.

To uninstall, navigate to the PolyglotDB directory and type :code:`pgdb uninstall`