import os

from polyglotdb import CorpusContext

# corpus_root = './data/LibriSpeech-aligned/'
# corpus_name = 'tutorial'
corpus_root = "./data/LibriSpeech-aligned-subset/"
corpus_name = "tutorial-subset"

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

print("Syllable enrichment...")
with CorpusContext(corpus_name) as c:
    c.encode_type_subset("phone", syllabics, "syllabic")
    c.encode_syllables(syllabic_label="syllabic")

print("Utterance enrichment...")
pause_labels = ["<SIL>"]
with CorpusContext(corpus_name) as c:
    c.encode_pauses(pause_labels)
    c.encode_utterances(min_pause_length=0.15)

print("Speaker enrichment...")
speaker_enrichment_path = os.path.join(corpus_root, "enrichment_data", speaker_filename)
with CorpusContext(corpus_name) as c:
    c.enrich_speakers_from_csv(speaker_enrichment_path)

print("Stress enrichment...")
lexicon_enrichment_path = os.path.join(corpus_root, "enrichment_data", stress_data_filename)

with CorpusContext(corpus_name) as c:
    c.enrich_lexicon_from_csv(lexicon_enrichment_path)
    c.encode_stress_from_word_property("stress_pattern")

print("Additional enrichment...")
with CorpusContext(corpus_name) as c:
    c.encode_rate("utterance", "syllable", "speech_rate")
    c.encode_count("word", "syllable", "num_syllables")
