.. _tshoot_install:

************
Installation (for Mac users) 
************

If the ``pgdb`` command does not work, you may try the following steps:

1. Uninstall Java
2. Make sure Anaconda is installed on your Mac. If you are using Miniconda, run ``miniconda install anaconda`` to install Anaconda. 
3. Reinstall Java by ``conda install -anaconda openjdk``. Note that you should not use Homebrew to install Java, since Anaconda helps to manage the Java version appropriate for PolyGlot installation. 
4. ``pgdb install``, ``pgdb start``, and ``pgdb stop`` should work now. 


