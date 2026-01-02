from polyglotdb import CorpusContext

# corpus_name = 'tutorial'
# export_path = './results/tutorial_3_output.csv'
corpus_name = "tutorial-subset"
export_path = "./results/tutorial_3_subset_output.csv"
# change export_path to the location where you want the CSV file to be saved

with CorpusContext(corpus_name) as c:
    q = c.query_graph(c.syllable)

    q = q.filter(c.syllable.stress == "1")
    q = q.filter(c.syllable.begin == c.syllable.word.begin)
    q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end)

    q = q.columns(
        c.syllable.label.column_name("syllable"),
        c.syllable.duration.column_name("syllable_duration"),
        c.syllable.word.label.column_name("word"),
        c.syllable.word.begin.column_name("word_begin"),
        c.syllable.word.end.column_name("word_end"),
        c.syllable.word.num_syllables.column_name("word_num_syllables"),
        c.syllable.word.stress_pattern.column_name("word_stress_pattern"),
        c.syllable.word.utterance.speech_rate.column_name("utterance_speech_rate"),
        c.syllable.speaker.name.column_name("speaker"),
        c.syllable.speaker.sex.column_name("speaker_sex"),
        c.syllable.discourse.name.column_name("file"),
    )
    print(f"Exporting full query to {export_path}")
    # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
    q = q.order_by(c.syllable.label)
    q.to_csv(export_path)

    print("Preview query limited to 10 data points...")
    q = q.limit(10)
    results = q.all()
    print(results)
