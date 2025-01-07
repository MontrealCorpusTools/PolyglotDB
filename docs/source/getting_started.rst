.. _ISCAN server: https://github.com/MontrealCorpusTools/ISCAN

.. _installation:

.. _Conda Installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html

.. _Reaper: https://github.com/google/REAPER

.. _Praat: https://www.fon.hum.uva.nl/praat/

.. _Docker: https://docs.docker.com/get-started/get-docker/
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

.. warning::

   On Windows, you must use the Anaconda Prompt or Miniforge Prompt to effectively manage and execute conda commands. 
   This is crucial to avoid potential issues specific to the Windows environment and to ensure that all functionalities work as intended.

To install via pip:

#. Create the a conda environment via :code:`conda create -n polyglotdb -c conda-forge openjdk=21 python=3.12 librosa`
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

.. _start_local_databases:

Steps to use PolyglotDB
-----------------------

Now that you have set up the PolyglotDB environment and installed local databases, 
follow these steps each time you use PolyglotDB:

#. Navigate to your working directory, either in your IDE or via the command line. (On Windows, use Anaconda Prompt/Miniforge Prompt.)
#. Activate the conda environment: :code:`conda activate polyglotdb`.
#. Start the local databases: :code:`pgdb start`.
#. Write your Python scripts inside this working directory.
#. Run the scripts using: :code:`python your_script.py`.
#. When finished, stop the local databases: :code:`pgdb stop`.
#. Deactivate the conda environment: :code:`conda deactivate`.

.. _docker_install:

Docker Environment
===================

Running PolyglotDB in a `Docker`_ container is a great way to maintain a consistent environment, isolate dependencies, and streamline your setup process. This section will guide you through setting up and using PolyglotDB within Docker.

Prerequisites
-------------

Before starting, ensure that Docker is installed on your system. You can check if Docker is installed and verify its version by running the following command in your terminal:

.. code:: bash

   docker version

Make sure your Docker Engine version is **19.03.0** or higher.

Setting Up the Docker Container
-------------------------------

Follow these steps to get your Docker container up and running:

1. **Clone the Repository:**

   First, clone the PolyglotDB Docker repository to your local machine: :code:`git clone https://github.com/MontrealCorpusTools/polyglotdb-docker.git`.

2. **Start the Docker Container:**

   Navigate to the directory you just cloned and start the container: :code:`docker-compose run polyglotdb`.

   .. note::

      **Note for Mac Users:**  
      If you're using a Mac, you might need to run :code:`docker compose run polyglotdb`

   This command launches an interactive shell inside the `polyglotdb` container, allowing you to execute PolyglotDB scripts directly.

3. **Working with the Default Folder Structure:**

   Your default folder structure is as follows. Ensure your Python scripts and data are placed within the `polyglotdb-docker` directory, which is mounted to the Docker container for execution:

   .. code-block:: text

      polyglotdb-docker (your default working directory, mounted to /polyglotdb inside the Docker container)
      ├── pgdb
      │   ├── neo4j
      │   │   ├── conf
      │   │   │   └── neo4j.conf
      │   │   ├── data
      │   │   │   └── *
      │   │   └── logs
      │   │       └── *
      │   ├── influxdb
      │   │   ├── conf
      │   │   │   └── influxdb.conf
      │   │   ├── data
      │   │   │   └── *
      │   │   └── meta
      │   │       └── *
      ├── your scripts and data should go here

4. **Editing and Running Your PolyglotDB Scripts**

   You can choose to edit your scripts either using an IDE outside of the Docker container or by using command-line text editors within the Docker container. Two text editors, ``nano`` and ``vim``, are pre-installed for use inside the container.

   - **Using an IDE Outside the Docker Container**:
     
     If you prefer to use an IDE outside the Docker container, 
     ensure that you save your scripts inside your working directory (default: ``polyglotdb-docker``). 
     You can customize this directory by following the instructions in the later section `Changing the Default Storage Location`_.
     The scripts stored in this directory will be automatically available inside the Docker container 
     under the ``/polyglotdb`` directory. You can then execute your scripts using the command: :code:`python your_script.py`.
  
   - **Using Command-Line Text Editors Inside the Docker Container**:
     
     If you choose to write your scripts inside the Docker container using command-line tools, 
     you can place them anywhere within the container and execute them using the command: :code:`python your_script.py`.
     However, if you want to preserve your scripts after shutting down the container, 
     ensure you save them in the directory mounted to your device (default: ``/polyglotdb``).

5. **Stopping the Docker Containers:**

   To stop the Docker containers, first exit the `polyglotdb` shell by running:

   .. code:: bash

      exit

   Then, shut down the other containers with:

   .. code:: bash

      docker compose down

.. _Changing the Default Storage Location:
Changing the Default Storage Location
-------------------------------------

You can modify the default folder structure by editing the `docker-compose.yml` file. To change the storage location for Neo4j and InfluxDB data:

1. Move the `neo4j` and `influxdb` folders from the `polyglotdb-docker/pgdb` directory to your desired location.

2. Update the volume paths in the `docker-compose.yml` file to reflect the new location. For example:

   .. code-block:: yaml

      neo4j:
         ...
         volumes:
            - /path/to/your/neo4j/conf:/conf
            - /path/to/your/neo4j/data:/data
            - /path/to/your/neo4j/logs:/logs
            - shared_data:/temp
         ...

      influxdb:
         ...
         volumes:
            - /path/to/your/influxdb:/var/lib/influxdb
            - /path/to/your/influxdb/conf/influxdb.conf:/etc/influxdb/influxdb.conf
            - shared_data:/temp
         ...

You can also change the working directory by modifying the `docker-compose.yml` file. For instance:

.. code-block:: yaml

   polyglotdb:
      ...
      volumes:
         - shared_data:/temp
         - /path/to/your/working/directory:/polyglotdb

By doing this, the specified directory on your device will be mounted to the Docker container under `/polyglotdb`. To access PolyglotDB scripts and data within the container, ensure they are placed inside your chosen directory.

Pre-installed Tools
-------------------

The Docker setup comes with several pre-installed tools inside the `polyglotdb` container located at `/pgdb/tools`:

1. `Praat`_: Installed at `/pgdb/tools/praat`, environment variable `praat`. In your script, you can reference it by :code:`os.environ.get('praat')`.
2. `Reaper`_: Installed at `/pgdb/tools/reaper`, environment variable `reaper`. In your script, you can reference it by :code:`os.environ.get('reaper')`.
