.. _ISCAN server: https://github.com/MontrealCorpusTools/ISCAN

.. _installation:

***************
Getting started
***************

PolyglotDB is the Python API for interacting with Polyglot databases and is installed through ``pip``. There are other
dependencies that must be installed prior to using a Polyglot database, depending on the user's platform.

.. note::

   Another way to use Polyglot functionality is through setting up an `ISCAN server`_.
   An Integrated Speech Corpus Analysis (ISCAN) server can be set up on a lab's central server, or you can run it on your
   local computer as well (though many
   of PolyglotDB's algorithms benefit from having more processors and memory available).  Please see the ISCAN
   documentation for more information on setting it up (http://iscan.readthedocs.io/en/latest/getting_started.html).
   The main feature benefits of ISCAN are multiple Polyglot databases (separating out different corpora and allowing any
   of them to be started or shutdown), graphical interfaces for inspecting data, and a user authentication system with different levels
   of permission for remote access through a web application.

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

Installing the PolyglotDB package also installs a utility script (``pgdb``) that is then callable from the command line
anywhere on the system.  The ``pgdb`` command allows for the administration of a single Polyglot database (install/start/stop/uninstall).
Using ``pgdb`` requires that several prerequisites be installed first, and the remainder of this section will detail how
to install these on various platforms.
Please be aware that using the ``pgdb`` utility to set up a database is not recommended for larger groups or those needing
remote access.
See the `ISCAN server`_ for a more fully featured solution.

Mac
```

#. Ensure Java 11 is installed inside Anaconda distribution (``conda install -c anaconda openjdk``) if using Anaconda, or
   via Homebrew otherwise (``brew cask install java``)
#. Check Java version is 11 via ``java --version``
#. Once PolyglotDB is installed, run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

.. warning::

   Do not use ``sudo`` with this command on Macs, as it will lead to permissions issues later on.

Once you have installed PolyglotDB, to start it run :code:`pgdb start`.
Likewise, you can close PolyglotDB by running :code:`pgdb stop`.

To uninstall, run :code:`pgdb uninstall`

Windows
```````

#. Ensure Java 11 is installed (https://www.java.com/) and on the path (``java --version`` works in the command prompt)
#. Check Java version is 11 via ``java --version``
#. Start an Administrator command prompt (right click on cmd.exe and select "Run as administrator"), as Neo4j will be installed as a Windows service.
#. Run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

To start the database, you likewise have to use an administrator command prompt before entering the commands :code:`pgdb start`
or :code:`pgdb stop`.

To uninstall, run :code:`pgdb uninstall` (also requires an administrator command prompt).

Linux
`````

Ensure Java 11 is installed. On Ubuntu:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install openjdk-11-jdk-headless

Once installed, double check that ``java --version`` returns Java 11. Then run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
:code:`pgdb install` to save data in the default directory.

Once you have installed PolyglotDB, to start it run :code:`pgdb start`.
Likewise, you can close PolyglotDB by running :code:`pgdb stop`.

To uninstall, navigate to the PolyglotDB directory and type :code:`pgdb uninstall`