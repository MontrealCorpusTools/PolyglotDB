from polyglotdb import CorpusContext
import csv
import os

if __name__ == '__main__':

    corpus_name = 'tutorial-subset'
    script_path = '/path/to/your/praat/script'
    export_path_1 = './results/tutorial_6_subset_voice_quality.csv'
    export_path_2 = './results/tutorial_6_subset_voice_quality_mean.csv'
    praat_path = "/usr/bin/praat"   # Make sure to check where Praat executable is stored on your device and change accordingly

    # 1. Perform voice quality analysis
    with CorpusContext(corpus_name) as c:
        c.reset_acoustic_measure('voice_quality')
        c.config.praat_path = praat_path
        # Properties in the script output to store
        props = [('H1_H2', float), ('H1_A1', float), ('H1_A2', float), ('H1_A3', float)]

        # Any custom arguments. 
        # Note: These arguments must be universal across all sound files. 
        # File specific arguments for example speaker gender are not yet supported
        # For example, in this script, it defines the number of measurements to take in each segment.
        arguments = [10]
        c.analyze_track_script('voice_quality', props, script_path, subset='vowel', annotation_type='phone', file_type='vowel', padding=0.1, arguments=arguments, call_back=print)

    # 2. Query and output analysis results
    print("Querying results...")
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.phone).filter(c.phone.subset=='vowel')
        q = q.columns(c.phone.label.column_name('label'), c.phone.begin.column_name('begin'), c.phone.end.column_name('end'), c.phone.voice_quality.track)
        q = q.order_by(c.phone.begin)
        results = q.all()
        print(results[0].track)
        q.to_csv(export_path_1)

    # 3. Encode statistics on the result 
    print("Calculating mean...")
    with CorpusContext(corpus_name) as c:
        # Statistics are stored in a dictionary 
        # key = (speaker, label)
        # value = (mean_H1H2, mean_H1A1, mean_H1A2, mean_H1A3)
        acoustic_statistics = c.get_acoustic_statistic('voice_quality','mean', by_annotation='phone', by_speaker=True)
        key = ('61', 'AO1')
        value = acoustic_statistics[key]
        print("speaker_word_pair: {}".format(key))
        print("mean measures: {}".format(value))

        # You may export this distionary to csv
        with open(export_path_2, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            header = ['speaker', 'vowel'] + [k for k, _ in next(iter(acoustic_statistics.values()))]
            writer.writerow(header)

            for (speaker, vowel), measures in acoustic_statistics.items():
                row = [speaker, vowel] + [v for _, v in measures]
                writer.writerow(row)