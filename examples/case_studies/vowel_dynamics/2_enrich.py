from polyglotdb import CorpusContext


def main():
    # Remember to change this if you changed it in step 1
    corpus_name = "ParlBleu-subset"

    # Specify the vowel set for this corpus
    vowel_set = [
        "a",
        "e",
        "i",
        "o",
        "u",
        "y",
        "ø",
        "œ",
        "œ̃",
        "ɑ",
        "ɑ̃",
        "ɔ",
        "ɔ̃",
        "ə",
        "ɛ",
        "ɛ̃",
        "ɜ",
    ]

    print("Encoding vowel set...")
    with CorpusContext(corpus_name) as c:
        c.encode_type_subset("phone", vowel_set, "vowel")

    print("Syllable enrichment...")
    with CorpusContext(corpus_name) as c:
        c.encode_type_subset("phone", vowel_set, "syllabic")
        c.encode_syllables(syllabic_label="syllabic")
        c.encode_count("word", "syllable", "num_syllables")

    print("Utterance enrichment...")
    # Specify the set of word labels which designate pauses
    pause_labels = ["<SIL>"]

    with CorpusContext(corpus_name) as c:
        c.encode_pauses(pause_labels)
        c.encode_utterances(min_pause_length=0.15)

    print("Speaker enrichment...")
    # Change this if you've moved the file on your computer
    speaker_enrichment_file = "../ParlBleu-subset/enrichment_data/speaker_metadata.csv"

    with CorpusContext(corpus_name) as c:
        c.enrich_speakers_from_csv(speaker_enrichment_file)


if __name__ == "__main__":
    main()
