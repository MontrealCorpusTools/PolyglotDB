.. _voice quality: https://linguistics.ucla.edu/people/keating/Keating_SST2006_talk.pdf

.. _UCLA Phonetics Lab: https://phonetics.linguistics.ucla.edu/

.. _Praat script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial/tutorial_6_vq_script.praat

.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_6.py

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_6_subset_voice_quality_mean.csv

.. _tutorial scripts: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial

.. _tutorial_vq:

*************************
Tutorial 6: Custom Script
*************************


This tutorial shows an example of applying a custom Praat script to make phonetic measures on an (already imported/enriched) PolyglotDB corpus.
We use the corpus from Tutorials 1-3, and apply a Praat script to extract spectral measures for `voice quality`_ analysis, including H1-H2, H1-A1, H1-A2, and H1-A3.  A time trajectory for each spectral measure is extracted for each vowel token.

The complete Python script for Tutorial  is available here: `tutorial scripts`_.


Workflow
========

**This tutorial assumes you have already run Tutorials 1 and 2**, which import and enrich the corpus with syllable, speaker, and utterance information.

Tutorial 6 can be followed in two ways, like other tutorials (see :ref:`here<tutorial_1_workflow>`):

* Pasting in commands one by one into the Python interpreter
* Running the entire script at once (``python tutorial_6.py``)

Running the whole script is the usual workflow for PolyglotDB, but the commands are shown one by one here to make it easier to follow along.

As in previous tutorials, ``import`` statements and the location of the corpus (``corpus_root``) must be set for the code in this tutorial
to be runnable.  (You also need to make sure the directory where you will save the CSV file, here ``results/``, exists.)

.. code-block:: python

    from polyglotdb import CorpusContext

    corpus_name = 'tutorial-subset'
    script_path = '/path/to/your/praat/script'
    export_path_1 = './results/tutorial_6_subset_voice_quality.csv'
    export_path_2 = './results/tutorial_6_subset_voice_quality_mean.csv'
    praat_path = "/usr/bin/praat"   # Make sure to check where Praat executable is stored on your device and change accordingly

.. _tutorial_vq_script:

The Example Praat script
=======================
The `Praat script`_ used for this analysis will extract H1-H2 and amplitude differences for higher harmonics (A1, A2, A3).
It is adopted from an online script from the `UCLA Phonetics Lab`_.

Each measure is extracted at 10 time points per vowel.

For more information on how to format your Praat script, check out (:ref:`custom_script_encoding`)

.. _tutorial_vq_analysis:

Performing VQ Analysis
======================

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        c.reset_acoustic_measure('voice_quality') # Reset exisiting acoustic measure
        c.config.praat_path = praat_path
        # Properties extracted from the Praat script
        props = [('H1_H2', float), ('H1_A1', float), ('H1_A2', float), ('H1_A3', float)]

        # Custom arguments (must be universal across all sound files)
        arguments = [10]  # Number of measurements per vowel
        c.analyze_track_script('voice_quality', props, script_path, subset='vowel', annotation_type='phone', file_type='vowel', padding=0.1, arguments=arguments, call_back=print)

.. note::

    When annotation_type is set to phone or word, some sound file segments may be too short for certain analyses.
    (For example, the Sound: To Pitch... command in Praat requires each segment to be longer than a minimum duration.)

    If you encounter such an error, you can try adding padding to the segments. The modified segments will have a new duration calculated as:
    :code:`duration = duration + 2 * padding`.

    However, ensure that your Praat script defines the analysis range correctly so that the measurements are performed within the original sound range.
    Any measurements obtained outside the segment's original time range will not be stored after the analysis is complete.

    The file_type parameter has three options based on resampled frequency upper bounds:
    16000Hz for ``consonant``, 11000Hz for ``vowel``, and 2000Hz for ``low_freq``.
    Choose the one that best fits your analysis range. By default, you can use consonant.

.. _tutorial_vq_query:

Querying results
================
After running the analysis, we can query and export the results to verify the extracted data.

The CSV file will contain the following columns:

- Phone label: The label of the phone.
- Begin/End time: The time range for the phone.
- Speaker information
- Current and following word information
- Voice quality measures: H1-H2, H1-A1, H1-A2, and H1-A3 values, as well as the timepoint at which they were measured.


.. code-block:: python

    # 2. Query and output analysis results
    print("Querying results...")
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.phone).filter(c.phone.subset=='vowel')
        q = q.columns(
            c.phone.label.column_name('label'),
            c.phone.begin.column_name('begin'),
            c.phone.end.column_name('end'),
            c.phone.speaker.name.column_name('speaker'),
            c.phone.speaker.sex.column_name('sex'),
            c.phone.discourse.name.column_name('discourse'),
            c.phone.word.following.transcription.column_name('following_word_transcription'),
            c.phone.word.label.column_name('word'),
            c.phone.word.begin.column_name('word_begin'),
            c.phone.word.end.column_name('word_end'),
            c.phone.voice_quality.track
             )
        q = q.order_by(c.phone.begin)
        results = q.all()

        # Display sample result
        print(results[0].track)

        # Export to CSV
        q.to_csv(export_path_1)



.. _tutorial_vq_statistics:

Calculating Mean Values
=======================
To understand the general trend, we can encode acoustic statistics (mean).

.. code-block:: python

    with CorpusContext(corpus_name) as c:
        acoustic_statistics = c.get_acoustic_statistic('voice_quality', 'mean', by_annotation='phone', by_speaker=True)

        # Display example result
        key = ('61', 'AO1')
        value = acoustic_statistics[key]
        print("speaker_word_pair: {}".format(key))
        print("mean measures: {}".format(value))

        # Export to CSV
        with open(export_path_2, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            header = ['speaker', 'vowel'] + [k for k, _ in next(iter(acoustic_statistics.values()))]
            writer.writerow(header)

            for (speaker, vowel), measures in acoustic_statistics.items():
                row = [speaker, vowel] + [v for _, v in measures]
                writer.writerow(row)


The CSV file generated will then be ready to open in other programs or in R for data analysis.

Note that the resulting CSV file, `tutorial_6_subset_voice_quality.csv`, contains measures at multiple time points per vowel.

You can see a `full version of the script`_ and its `expected output`_ when run on the 'LibriSpeech-subset' corpora.

Next steps
==========


This tutorial uses a Praat script to do *dynamic* analysis: tracks for each measure (H1-H2) for each vowel, as a function of time, are generated and stored in the database.

:ref:`Case Study 4<case_study_praat>` shows an example of using a Praat script for static analysis, where one value per acoustic measure (e.g. H1-H2 average, across a vowel) is stored in the database.
