import os
from argparse import ArgumentParser

import polyglotdb.io as pgio
from polyglotdb import CorpusContext

corpus_root = "./LibriSpeech-aligned"
corpus_name = "tutorial"

speaker_filename = "SPEAKERS.csv"
stress_data_filename = "iscan_lexicon.csv"

syllabics = [
    "ER0",
    "IH2",
    "EH1",
    "AE0",
    "UH1",
    "AY2",
    "AW2",
    "UW1",
    "OY2",
    "OY1",
    "AO0",
    "AH2",
    "ER1",
    "AW1",
    "OW0",
    "IY1",
    "IY2",
    "UW0",
    "AA1",
    "EY0",
    "AE1",
    "AA0",
    "OW1",
    "AW0",
    "AO1",
    "AO2",
    "IH0",
    "ER2",
    "UW2",
    "IY0",
    "AE2",
    "AH0",
    "AH1",
    "UH2",
    "EH2",
    "UH0",
    "EY1",
    "AY0",
    "AY1",
    "EH0",
    "EY2",
    "AA2",
    "OW2",
    "IH1",
]

pause_labels = ["<SIL>"]

export_path = "./vowel_duration_output.csv"

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    speaker_enrichment_path = os.path.join(corpus_root, "enrichment_data", speaker_filename)
    lexicon_enrichment_path = os.path.join(corpus_root, "enrichment_data", stress_data_filename)

    parser = pgio.inspect_mfa(corpus_root)
    parser.call_back = print

    if args.reload:
        with CorpusContext(corpus_name) as c:
            c.reset()
            print("Loading data...")
            c.load(parser, corpus_root)

            print("Encoding syllables...")
            c.encode_type_subset("phone", syllabics, "syllabic")
            c.encode_syllables(syllabic_label="syllabic")

            print("Encoding utterances...")
            c.encode_pauses(pause_labels)
            c.encode_utterances(min_pause_length=0.15)

            print("Encoding speakers...")
            c.enrich_speakers_from_csv(speaker_enrichment_path)

            print("Encoding lexicon...")
            c.enrich_lexicon_from_csv(lexicon_enrichment_path)
            c.encode_stress_from_word_property("stress_pattern")

            print("Encoding rate...")
            c.encode_rate("utterance", "syllable", "speech_rate")

    with CorpusContext(corpus_name) as c:
        print("Generating query...")
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
            c.syllable.discourse.name.column_name("file"),
        )

        print("Writing query to file...")
        q.to_csv(export_path)
