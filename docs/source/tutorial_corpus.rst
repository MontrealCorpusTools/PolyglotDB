.. _LibriSpeech: http://www.openslr.org/12/

.. _THCHS-30: https://openslr.org/18/

.. _Montreal Forced Aligner (MFA): https://montreal-forced-aligner.readthedocs.io/en/latest/

.. _tutorial corpus download: https://mcgill-my.sharepoint.com/:f:/g/personal/morgan_sonderegger_mcgill_ca/EipFbcOfR31JnM4XYprp14oBuYW9lYA9IzOBcEERFZxwyA?e=tiV8bW

.. _tutorial_download:

Downloading the tutorial corpus
===============================

The following tutorials are written to work with two example English corpora. These are both subsets of the `LibriSpeech`_ test-clean dataset, forced aligned with the `Montreal Forced Aligner (MFA)`_:

* The larger corpus, ``LibriSpeech-aligned``, contains dozens of speakers and 490MB of data.
* The smaller corpus, ``LibriSpeech-aligned-subset``, contains just two speakers from the previous corpus and therefore much less data (25MB).

The corpora are made available for download `here <https://mcgill-my.sharepoint.com/:f:/g/personal/morgan_sonderegger_mcgill_ca/EipFbcOfR31JnM4XYprp14oBuYW9lYA9IzOBcEERFZxwyA?e=tiV8bW>`_


All tutorials in the documentation currently use the smaller corpus, so you can quickly test while getting used to interacting with PolyglotDB.

..  since some enrichment commands can be time-consuming when run on large datasets.

For a more realistic experience and more interesting results, you can alternatively use the larger corpus, by changing the top of each tutorials's code (corpus name, path to data location).



Alternative example corpora
```````````````


A good exercise for getting familiar with PolyglotDB is to adapt the provided tutorial scripts for use on other corpora. To this end, the following example corpora for other languages have also been aligned with MFA and made available:

* Small and large subsets of the `THCHS-30`_ corpus of Mandarin, available at the same link as above: ``thchs30-subset-small`` (2 speakers, 43MB) and ``thchs30-subset-large`` (30 speakers, 646MB).
* A small subset of the ParlBleu corpus of Quebec French (6 speakers, 716MB), available `here <https://github.com/massimolipari/ParlBleu-subset>`_.
