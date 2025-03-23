.. _voice quality: https://linguistics.ucla.edu/people/keating/Keating_SST2006_talk.pdf

.. _UCLA Phonetics Lab: https://phonetics.linguistics.ucla.edu/

.. _script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/main/examples/tutorial/tutorial_6_vq_script.praat

.. _full version of the script: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/tutorial_6.py

.. _expected output: https://github.com/MontrealCorpusTools/PolyglotDB/tree/master/examples/tutorial/results/tutorial_6_subset_voice_quality_mean.csv

.. _tutorial_vq:

*************************
Tutorial 6: Custom Script 
*************************

The main objective of this tutorial is to perform `voice quality`_ analysis on the corpus using a Praat script and extract 
spectral measures like H1-H2, H1-A1, H1-A2, and H1-A3.

As in the other tutorials, import statements and the corpus name (as it is stored in pgdb) must be set for the code in this tutorial
to be runnable. The example given below continues to make use of the "tutorial-subset" corpus we have been using in tutorials 1-5.

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
- Voice quality measures: H1-H2, H1-A1, H1-A2, and H1-A3 values.


.. code-block:: python 

    # 2. Query and output analysis results
    print("Querying results...")
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.phone).filter(c.phone.subset=='vowel')
        q = q.columns(c.phone.label.column_name('label'), c.phone.begin.column_name('begin'), c.phone.end.column_name('end'), c.phone.voice_quality.track)
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


The CSV file generated will then be ready to open in other programs or in R for data analysis. You can see a `full version of the script`_ and its `expected output`_ when run on the 'LibriSpeech-subset' corpora.
