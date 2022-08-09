.. _tshoot_tut:

************
Tutorials
************

Corpus Structure
===============

* Your corpus should be arranged by speaker. 
* Each speaker directory contains TextGrid files and the corresponding wav files. If some corresponding wav files are missing, the ``KeyError: 'vowel_file_path'`` may appear. 
* If the KeyError still exists, you may reset the corpus as below. 

.. code-block:: python 
    with CorpusContext(corpus_name) as c:
        c.reset()


Defining Vowel Set (Tutorial 4)
===============

**In vowel formant analysis, make sure to check the output of the phone set, and accordingly define your own vowel set.** This is because, in Tutorial 4, the regex used to define the vowel set may not work for the language you are working on. 

In other words, instead of using:

.. code-block:: python
    vowel_set = [re.search(vowel_regex, p).string for p in phone_set
            if re.search(vowel_regex, p) != None and p not in non_speech_set]


Use (e.g., for Cantonese): 

.. code-block:: python 
    vowel_set = ['6', '6j', '6w', '9', '9y', 'E:', 'O:', 'O:j', 'a:', 'a:j', 'a:w', 'ej', 'i:', 'ow', 'u:', 'y:']


You can either use your own regex or type the vowels manually based the output of the phone set. 


