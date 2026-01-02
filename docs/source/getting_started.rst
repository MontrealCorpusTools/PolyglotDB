.. _ISCAN documentation: https://iscan.readthedocs.io/en/latest/

.. _ISCAN: https://github.com/MontrealCorpusTools/ISCAN

.. _Conda Installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html

.. _Reaper: https://github.com/google/REAPER

.. _Praat: https://www.fon.hum.uva.nl/praat/

.. _Docker: https://docs.docker.com/get-started/get-docker/

.. _installation:

***************
Getting started
***************

.. PolyglotDB is the Python API for interacting with Polyglot databases and is installed through ``conda-forge`` or ``pip``.

.. _actual_install:

Installation
============

PolyglotDB is now available directly via conda-forge. We recommend using Conda for installation, as it ensures compatibility with required system dependencies like Java and makes it easier to manage environments across platforms.

If you don't have conda installed on your device:

#. Install either Anaconda, Miniconda, or Miniforge (`Conda Installation`_)
#. Make sure your conda is up to date :code:`conda update conda`

.. _add_conda_to_path:

.. Note::

   On Windows, it is recommended to use the Anaconda Prompt or Miniforge Prompt to manage and execute conda commands effectively.
   This is because, by default, installing Anaconda or Miniforge does not add the ``conda`` command to your system's PATH environment variable.
   However, if you prefer to use the regular Windows Command Prompt or run Python scripts directly from your IDE, you will need to manually add the necessary directories to your PATH.
   To do so, follow these steps:

      #. Open the Start Menu and search for ``Environment Variables``.
      #. Click on ``Edit the system environment variables``.
      #. In the System Properties window, click on the ``Environment Variables`` button.
      #. In the Environment Variables window, find the ``Path`` variable in the ``User variables`` or ``System variables`` section and select it.
      #. Click ``Edit``, then ``New``, and add the following two paths (adjust to your installation):

         #. ``C:\Users\YourUsername\Anaconda3``
         #. ``C:\Users\YourUsername\Anaconda3\Scripts``

   After completing these steps, you should be able to use conda in the Windows Command Prompt and configure your IDE accordingly.

Pathway to installation
-----------------------

There are two mandatory steps to install PolyglotDB:

1. Either :ref:`Quick Installation<quick_install>` via ``conda-forge`` **or** :ref:`Installation from source with pip<pip_install>`

2. :ref:`Setting up a local database<local_setup>`

Optionally, you can :ref:`Configure Your IDE<configure_IDE>` between Step 1 and Step 2.


.. _quick_install:

Quick Installation via conda-forge (Recommended)
------------------------------------------------

#. You can install PolyglotDB using a single Conda command :code:`conda create -n polyglotdb -c conda-forge polyglotdb`
#. Activate conda environment :code:`conda activate polyglotdb`

.. _pip_install:

To install from source (primarily for development)
-------------------------------------------------
.. note::

   Skip this step if you have installed PolyglotDB via conda-forge

#. Clone or download the Git repository (https://github.com/MontrealCorpusTools/PolyglotDB).
#. Navigate to the directory via command line and create the conda environment via :code:`conda env create -f environment.yml`
#. Activate conda environment :code:`conda activate polyglotdb-dev`
#. Install PolyglotDB via :code:`pip install -e .`, which will install the ``pgdb`` utility that can be run inside your conda environment
   and manages a local database.

(Note that if you installed via conda-forge, the ``pgdb`` utility is already installed.)



.. _configure_IDE:

Configure Your IDE (Optional)
-----------------------------

.. note::

    This step is not required for general use of PolyglotDB. You only need to do this if you plan
    to write/run PolyglotDB scripts within an IDE, such as Visual Studio Code, PyCharm, or similar tools.

If you are using an IDE, you may encounter issues where the IDE's default Python interpreter is different from the one set up in your Conda environment.
This can lead to errors such as missing packages, even if you've installed everything correctly in Conda.
In such cases, you need to manually set the Python interpreter in your IDE to point to the one used by your Conda environment.
If you are on Windows, make sure you have completed :ref:`this step<add_conda_to_path>` so that the Conda environment is accessible from your IDE's terminal.
For Visual Studio Code, follow these steps (a similar process applies to most other IDEs):

   #. Make sure you have the Python extension installed in VSCode.
   #. Open VSCode and open Command Palette (``Ctrl+Shift+p`` on Windows or ``cmd+shift+p`` on Mac), then choose ``Python: Select Interpreter``.
   #. Select the interpreter corresponding to your Conda environment (e.g., ``conda-env:polyglotdb``).
   #. Open a new terminal in VSCode. If the environment is not activated automatically, run :code:`conda activate polyglotdb`

Now, you can run PolyglotDB commands and scripts directly within VSCode's integrated terminal.

.. _local_setup:

Setting up local database
-------------------------

Installing the PolyglotDB package also installs a utility script (``pgdb``) that is then callable from the command line inside your conda environment.
The ``pgdb`` command allows for the administration of a single Polyglot database (install/start/stop/uninstall).
``pgdb install`` is a separate step that installs the actual local database backend, including Neo4j and InfluxDB. This is necessary to run PolyglotDB locally.

**You only need to run** :code:`pgdb install` **once**. After it is installed, you only ever use the commands in :ref:`managing_the_local_database` to interact with PolyglotDB databases.

Installing the local database
`````````````````````````````

#. Make sure you are inside the dedicated conda environment just created. If not, activate it via :code:`conda activate polyglotdb`
#. Inside your conda environment, run :code:`pgdb install /path/to/where/you/want/data/to/be/stored`, or
   :code:`pgdb install` to save data in the default directory.

.. Warning::
   #. On Windows, make sure you are running as an Administrator (right-click on Anaconda Prompt/Miniforge Prompt/Command Prompt/Your IDE and select "Run as administrator"), as Neo4j will be installed as a Windows service.
   #. Do not use ``sudo`` with ``pgdb install`` on macOS, as it will lead to permissions issues later on.

.. _managing_the_local_database:
Managing the local database
```````````````````````````

* To start the database: :code:`pgdb start`
* To stop the database: :code:`pgdb stop`
* To uninstall the database :code:`pgdb uninstall`


To view your conda environments:

.. code-block:: bash

    conda info -e

To return to your root environment:

.. code-block:: bash

    conda deactivate

.. _start_local_databases:

Steps to use PolyglotDB
=======================

Now that you have set up the PolyglotDB conda environment and installed local databases,
follow these steps each time you use PolyglotDB:

#. Navigate to your working directory, either in your IDE or via the command line.
#. Activate the conda environment: :code:`conda activate polyglotdb`.
#. Start the local databases: :code:`pgdb start`.
#. Put your Python scripts (which use the :code:`polyglotdb` library) inside this working directory.
#. Run the scripts using: :code:`python your_script.py`.
#. When finished, stop the local databases: :code:`pgdb stop`.
#. Deactivate the conda environment: :code:`conda deactivate`.

.. _docker_install:

Alternative Installation (Using Docker Environment)
===================================================

Running PolyglotDB in a `Docker`_ container is a great way to maintain a consistent environment, isolate dependencies, and streamline your setup process.
This section will guide you through setting up and using PolyglotDB within Docker. Note that this method is an alternative to the default installation with conda-forge or pip.
If you already installed via conda-forge or pip above, **do not re-install with Docker**.

Prerequisites
-------------

Before starting, ensure that Docker is installed on your system. You can check if Docker is installed by running the following command in your terminal:

.. code:: bash

   docker version

Setting Up the Docker Container
-------------------------------

Follow these steps to get your Docker container up and running:

1. **Clone the Repository:**

   First, clone the PolyglotDB Docker repository to your local machine:

   :code:`git clone https://github.com/MontrealCorpusTools/polyglotdb-docker.git`

2. **Start the Docker Container:**

   Navigate to the directory you just cloned and start the container:

   :code:`docker-compose run polyglotdb`

   .. note::

      **Note for Mac Users:**
      If you're using a Mac, you might need to run :code:`docker compose run polyglotdb`

   The docker compose run automatically starts the databases server, so there's no extra steps to set up the databases.
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

   - **Note when writing your scripts**:

      #. It is important to **avoid** using absolute paths in your scripts when working with Docker.
         This is because the Docker container has its own internal filesystem, so absolute paths from your host machine
         (e.g., ``/home/user/documents/my_corpus``) will not be valid inside the container.
         Instead, always use relative paths based on the current working directory inside the container.
         Additionally, you must place all files you want to reference (such as corpus folders, Praat scripts, etc.)
         inside the directory that is mounted to the Docker container, which is the ``polyglotdb-docker`` directory by default.

      .. code:: python

         import os
         corpus_root = './data/my_corpus'
         # Now you can use corpus_root to access files in the my_corpus folder

      #. The Docker setup comes with several pre-installed tools inside the `polyglotdb` container located at `/pgdb/tools`:

         1. `Praat`_: Installed at `/pgdb/tools/praat`, environment variable `praat`. In your script, you can reference it by :code:`os.environ.get('praat')`.
         2. `Reaper`_: Installed at `/pgdb/tools/reaper`, environment variable `reaper`. In your script, you can reference it by :code:`os.environ.get('reaper')`.



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
