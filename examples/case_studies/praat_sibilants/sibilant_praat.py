import os
from argparse import ArgumentParser
from pathlib import Path

import polyglotdb.io as pgio
from polyglotdb import CorpusContext

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

sibilant_segments = ["S", "Z", "SH", "ZH"]

sibilant_script_path = "./praat_sibilant.praat"
praat_path = "/usr/bin/praat"

export_path = "./sibilant_spectral_output.csv"

if __name__ == "__main__":
    argument_parser = ArgumentParser()
    argument_parser.add_argument("corpus", type=Path)
    argument_parser.add_argument("--reload", action="store_true")
    args = argument_parser.parse_args()

    corpus_root = str(args.corpus)
    corpus_name = args.corpus.stem

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
        if not c.hierarchy.has_token_property("phone", "cog"):
            print("Enriching sibilants...")
            c.encode_class(sibilant_segments, "sibilant")
            c.analyze_script(
                annotation_type="phone",
                subset="sibilant",
                script_path=sibilant_script_path,
                duration_threshold=0.01,
            )

    with CorpusContext(corpus_name) as c:
        print("Generating query...")
        q = c.query_graph(c.phone).filter(c.phone.subset == "sibilant")
        q = q.filter(c.phone.begin == c.phone.syllable.word.begin)

        q = q.columns(
            c.phone.id.column_name("phone_id"),
            c.phone.label.column_name("phone_label"),
            c.phone.duration.column_name("phone_duration"),
            c.phone.begin.column_name("phone_begin"),
            c.phone.end.column_name("phone_end"),
            c.phone.following.label.column_name("following_phone_label"),
            c.phone.previous.label.column_name("previous_phone_label"),
            c.phone.syllable.label.column_name("syllable_label"),
            c.phone.syllable.stress.column_name("syllable_stress"),
            c.phone.syllable.duration.column_name("syllable_duration"),
            c.phone.syllable.phone.filter_by_subset("onset").label.column_name("onset"),
            c.phone.syllable.phone.filter_by_subset("nucleus").label.column_name("nucleus"),
            c.phone.syllable.phone.filter_by_subset("coda").label.column_name("coda"),
            c.phone.syllable.word.label.column_name("word_label"),
            c.phone.syllable.word.begin.column_name("word_begin"),
            c.phone.syllable.word.end.column_name("word_end"),
            c.phone.syllable.word.utterance.speech_rate.column_name("utterance_speech_rate"),
            c.phone.syllable.speaker.name.column_name("speaker"),
            c.phone.syllable.discourse.name.column_name("file"),
            c.phone.cog.column_name("cog"),
            c.phone.peak.column_name("peak"),
        )

        print("Writing query to file...")
        q.to_csv(export_path)
