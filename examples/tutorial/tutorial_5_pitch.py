import os
import re

from polyglotdb import CorpusContext

if __name__ == "__main__":
    # corpus_root = './data/LibriSpeech-aligned/'
    # corpus_name = 'tutorial'
    # export_path = './results/tutorial_5_pitch.csv')
    corpus_root = "./data/LibriSpeech-aligned-subset/"
    corpus_name = "tutorial-subset"
    export_path = "./results/tutorial_5_subset_pitch.csv"

    ## 1. ENRICHMENT TO ENCODE SYLLABLES, UTTERANCES, SPEAKERS ##
    # NOTE: Step 1 is duplicated in tutorial 4. If have completed tutorial 4, you
    # can comment/delete code below for encoding syllables/utterances/speakers

    with CorpusContext(corpus_name) as c:
        q = c.query_lexicon(c.lexicon_phone)
        q = q.order_by(c.lexicon_phone.label)
        q = q.columns(c.lexicon_phone.label.column_name("phone"))
        phone_results = q.all()
    phone_set = [x.values[0] for x in phone_results]

    non_speech_set = ["<SIL>", "sil", "spn"]

    vowel_regex = "^[AEOUI].[0-9]"
    vowel_set = [
        re.search(vowel_regex, x).string
        for x in phone_set
        if re.search(vowel_regex, x) is not None
    ]

    print("Encoding vowel set...")
    with CorpusContext(corpus_name) as c:
        c.encode_type_subset("phone", vowel_set, "vowel")

    print("Encoding vowel syllables...")
    with CorpusContext(corpus_name) as c:
        c.encode_syllables(syllabic_label="vowel")

    with CorpusContext(corpus_name) as c:
        c.encode_pauses(non_speech_set)
        c.encode_utterances(min_pause_length=0.15)

    print("Speaker enrichment begun...")
    speaker_enrichment_path = os.path.join(corpus_root, "enrichment_data", "SPEAKERS.csv")
    with CorpusContext(corpus_name) as c:
        c.enrich_speakers_from_csv(speaker_enrichment_path)

    ## 2. ENCODE PITCH TRACKS

    # And now for something else! Let's get pitch tracks from the data.
    # We encode syllable count per word - this will be useful when we look at the pitch tracks.
    with CorpusContext(corpus_name) as c:
        c.encode_count("word", "syllable", "num_syllables")

    # Pitch encoding
    # This step uses Praat, a program for analyzing audio files
    # The PATH for running the Praat command on your machine needs to be used.
    print("Encoding pitch...")
    with CorpusContext(corpus_name) as c:
        c.reset_acoustic_measure("pitch")
        c.config.praat_path = "/usr/bin/praat"
        metadata = c.analyze_pitch(algorithm="speaker_adapted", call_back=print)

    ## 3. DO QUERY, EXPORT TO CSV

    with CorpusContext(corpus_name) as c:
        ## phone comes at beginning of utterance
        q = c.query_graph(c.phone).filter(c.phone.word.begin == c.phone.word.utterance.begin)
        ## restrict just to phone = vowels
        q = q.filter(c.phone.subset == "vowel")
        ## preceding phone is at beginning of the word
        q = q.filter(c.phone.previous.begin == c.phone.word.begin)
        q = q.columns(
            c.phone.id.column_name("traj_id"),
            c.phone.label.column_name("vowel"),
            c.phone.previous.label.column_name("consonant"),
            c.phone.following.label.column_name("following_phone"),
            c.phone.word.label.column_name("word"),
            c.phone.word.duration.column_name("word_duration"),
            c.phone.word.transcription.column_name("word_transcription"),
            c.phone.word.following.transcription.column_name("following_word_transcription"),
            c.phone.begin.column_name("begin"),
            c.phone.end.column_name("end"),
            c.phone.discourse.name.column_name("discourse"),
            c.phone.speaker.name.column_name("speaker"),
            c.phone.speaker.sex.column_name("sex"),
            c.phone.pitch.track.column_name("f0"),
        )

        # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
        q = q.order_by(c.phone.label)
        results = q.all()
        q.to_csv(export_path)
        print(f"Results exported to {export_path}")
