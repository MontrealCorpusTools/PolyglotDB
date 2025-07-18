.. _LibriSpeech: http://www.openslr.org/12/

.. _Montreal Forced Aligner: https://montreal-forced-aligner.readthedocs.io/en/latest/

.. _tutorial corpus download: https://mcgill-my.sharepoint.com/:f:/g/personal/morgan_sonderegger_mcgill_ca/EipFbcOfR31JnM4XYprp14oBuYW9lYA9IzOBcEERFZxwyA?e=tiV8bW


.. _tutorial_download:

Downloading the tutorial corpus
===============================

These are both subsets of the `LibriSpeech`_ test-clean dataset, forced aligned with the `Montreal Forced Aligner`_:

* The larger corpus, ``LibriSpeech-aligned``, contains dozens of speakers and 490MB of data. 
* The smaller corpus, ``LibriSpeech-aligned-subset``, contains just two speakers from the previous corpus and therefore much less data (25MB).

The corpora are made available for download here: `tutorial corpus download`_. 

In tutorials 1-3, the smaller corpus is a better choice so that you can quickly test commands while getting used to interacting with polyglotdb, since some enrichment commands can be timeconsuming when run on large datasets.

Tutorials 4-6 should be performed using the larger corpus to allow for more coherent results.



