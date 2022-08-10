.. _tshoot_other:

************
Others
************

Run time error 
===============

If this error occurs: 

.. code-block:: python 
    
    RuntimeError: 
        An attempt has been made to start a new process before the
        current process has finished its bootstrapping phase.

        This probably means that you are not using fork to start your
        child processes and you have forgotten to use the proper idiom
        in the main module:

            if __name__ == '__main__':
                freeze_support()
                ...

        The "freeze_support()" line can be omitted if the program
        is not going to be frozen to produce an executable.


You need to add ``if __name__ == '__main__'`` at the beginning of your vowel-formant.py file.



