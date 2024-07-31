.. _ISCAN server: https://github.com/MontrealCorpusTools/ISCAN

.. _installation:

.. _Conda Installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html

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

It is recommended to create an insolated conda environment for using PolyglotDB, for ensuring the correct Java version as well as better package management with Python. 

If you don't have conda installed on your device: 

#. Install either Anaconda, Miniconda, or Miniforge (`Conda Installation`_)
#. Make sure your conda is up to date :code:`conda update conda`

.. note::
   On Windows, you should use Anaconda Prompt or Miniforge Prompt in order to use conda.

To install via pip:

#. Create the a conda environment via :code:`conda create -n polyglotdb -c conda-forge openjdk pip`
#. Activate conda environment :code:`conda activate polyglotdb`
#. Install PolyglotDB via :code:`pip install polyglotdb`, which will install the ``pgdb`` utility that can be run inside your conda environment 
   and manages a local database.

To install from source (primarily for development):

#. Clone or download the Git repository (https://github.com/MontrealCorpusTools/PolyglotDB).
#. Navigate to the directory via command line and create the conda environment via :code:`conda env create -f environment.yml`
#. Activate conda environment :code:`conda activate polyglotdb-dev`
#. Install PolyglotDB via :code:`pip install -e .`, which will install the ``pgdb`` utility that can be run inside your conda environment
   and manages a local database.

.. _local_setup:

Set up local database
---------------------

Installing the PolyglotDB package also installs a utility script (``pgdb``) that is then callable from the command line inside your conda environment. 
The ``pgdb`` command allows for the administration of a single Polyglot database (install/start/stop/uninstall).
Using ``pgdb`` requires that several prerequisites be installed first, and the remainder of this section will detail how
to install these on various platforms.
Please be aware that using the ``pgdb`` utility to set up a database is not recommended for larger groups or those needing
remote access.
See the `ISCAN server`_ for a more fully featured solution.

Mac & Linux
```````````
#. Make sure you are inside the dedicated conda environment just created. If not, activate it via :code:`conda activate polyglotdb`
#. Inside your conda environment, run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

.. warning::

   Do not use ``sudo`` with this command on Macs, as it will lead to permissions issues later on.

Once you have installed PolyglotDB, to start it run :code:`pgdb start`.
Likewise, you can close PolyglotDB by running :code:`pgdb stop`.

To uninstall, run :code:`pgdb uninstall`

Windows
```````

#. Make sure you are running as an Administrator (right-click on Anaconda Prompt/Miniforge Prompt and select "Run as administrator"), as Neo4j will be installed as a Windows service.
#. If you had to reopen a command prompt in Step 1, reactivate your conda environment via: :code:`conda activate polyglotdb`.
#. Inside your conda environment, run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

To start/stop the database, you likewise have to use an administrator command prompt before entering the commands :code:`pgdb start`
or :code:`pgdb stop`.

To uninstall, run :code:`pgdb uninstall` (also requires an administrator command prompt).


To view your conda environments:

.. code-block:: bash

    conda info -e

To return to your root environment:

.. code-block:: bash

    conda deactivate
