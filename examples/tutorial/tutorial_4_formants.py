import re

from polyglotdb import CorpusContext

if __name__ == "__main__":
    # corpus_root = './data/LibriSpeech-aligned/'
    # corpus_name = 'tutorial'
    # export_path = './results/tutorial_4_formants.csv')
    corpus_root = "./data/LibriSpeech-aligned-subset/"
    corpus_name = "tutorial-subset"
    export_path = "./results/tutorial_4_subset_formants.csv"

    # retrieve phone set for vowel processing
    with CorpusContext(corpus_name) as c:
        q = c.query_lexicon(c.lexicon_phone)
        q = q.order_by(c.lexicon_phone.label)
        q = q.columns(c.lexicon_phone.label.column_name("phone"))
        phone_results = q.all()
    phone_set = [x.values[0] for x in phone_results]

    # specify non-speech phones for this corpus:
    non_speech_set = ["<SIL>", "sil", "spn"]

    # in turn, use a regular expression to find all the vowel phones
    vowel_regex = "^[AEOUI].[0-9]"
    vowel_set = [
        re.search(vowel_regex, x).string
        for x in phone_set
        if re.search(vowel_regex, x) is not None and x not in non_speech_set
    ]

    # we now enrich the corpus with syllable annotations
    # to do this, we create a phone subset called vowel
    # containing all vowel phones
    print("Encoding vowel set...")
    with CorpusContext(corpus_name) as c:
        c.encode_type_subset("phone", vowel_set, "vowel")

    # we now enrich the corpus with syllables that have
    # vowels as their nuclei
    print("Encoding vowel syllables...")
    with CorpusContext(corpus_name) as c:
        c.encode_syllables(syllabic_label="vowel")

    # This step uses Praat, a program for analyzing audio files
    # The PATH for running the Praat command on your machine needs to be used.
    print("Formant calculations...")
    with CorpusContext(corpus_name) as c:
        c.config.praat_path = "/usr/bin/praat"
        c.analyze_formant_points(vowel_label="vowel", call_back=print)

    print("Querying results...")
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.phone).filter(c.phone.subset == "vowel")
        q = q.columns(
            c.phone.speaker.name.column_name("speaker"),
            c.phone.speaker.sex.column_name("speaker_sex"),
            c.phone.discourse.name.column_name("file"),
            c.phone.utterance.speech_rate.column_name("speech_rate"),
            c.phone.word.label.column_name("word"),
            c.phone.label.column_name("phone"),
            c.phone.previous.label.column_name("previous"),
            c.phone.following.label.column_name("following"),
            c.phone.begin.column_name("phone_start"),
            c.phone.end.column_name("phone_end"),
            c.phone.F1.column_name("F1"),
            c.phone.F2.column_name("F2"),
            c.phone.F3.column_name("F3"),
        )

        # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
        q = q.order_by(c.phone.label)
        results = q.all()
        q.to_csv(export_path)
