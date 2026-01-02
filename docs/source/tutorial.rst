
.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial/results

.. _tutorials:

********
Tutorials
********
========

These tutorials walk you through the basic workflow of using PolyglotDB, from setting up a corpus to extracting acoustic measurements.

**Tutorials 1–3** form a complete analysis and should be done in order. They show you how to import a small speech corpus, enrich it with information like syllables and utterances, and extract structured results.

**Tutorials 4-6** are independent. They cover additional types of acoustic analysis—formant tracking for vowels, pitch analysis, and applying a custom Praat script (to analyze voice quality, in this example). You can do these in any order.

- **Note**: each of Tutorials 4-6  assumes that you have first run Tutorials 1-2 (which import and enrich the corpus).

Before doing any tutorial you need to download one or both tutorial corpora.

For all tutorials, you can compare your results with the `expected output`_.

If at any point there’s some error or interruption in import or other stages of the tutorial, you should :ref:`reset the database<resetting>`.




.. toctree::
   :maxdepth: 1

   tutorial_corpus.rst
   tutorial_first_steps.rst
   tutorial_enrichment.rst
   tutorial_query.rst
   tutorial_formants.rst
   tutorial_pitch.rst
   tutorial_custom_script.rst
