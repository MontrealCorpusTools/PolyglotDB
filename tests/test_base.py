import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.io import inspect_mfa, inspect_textgrid


def test_load_discourse(graph_db, mfa_test_dir, textgrid_test_dir):
    test_file_path = os.path.join(mfa_test_dir, "mfa_test.TextGrid")
    acoustic_path = os.path.join(textgrid_test_dir, "acoustic_corpus.TextGrid")
    mfa_parser = inspect_mfa(test_file_path)
    parser = inspect_textgrid(acoustic_path)
    with CorpusContext("load_remove_test", **graph_db) as c:
        c.reset()
        c.load_discourse(parser, acoustic_path)
        c.load_discourse(mfa_parser, test_file_path)

        syllabics = ["ER", "AE", "IH", "EH", "ae", "ih", "er", "eh"]
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables()

        q = c.query_graph(c.word).filter(c.word.label == "JURASSIC")
        assert q.count() > 0
        q = c.query_graph(c.phone).filter(c.phone.label == "AE")
        assert q.count() > 0
        q = c.query_lexicon(c.syllable).filter(c.syllable.label == "JH.ER")
        assert q.count() > 0

        q = c.query_lexicon(c.lexicon_word).filter(c.lexicon_word.label == "JURASSIC")
        assert q.count() > 0
        q = c.query_lexicon(c.lexicon_phone).filter(c.lexicon_phone.label == "AE")
        assert q.count() > 0
        q = c.query_lexicon(c.lexicon_phone).filter(c.lexicon_phone.label == "ae")
        assert q.count() > 0
        q = c.query_lexicon(c.lexicon_syllable).filter(c.lexicon_syllable.label == "JH.ER")
        assert q.count() > 0

        q = c.query_discourses().filter(c.discourse.name == "mfa_test")
        assert q.count() > 0
        q = c.query_speakers().filter(c.speaker.name == "mfa")
        assert q.count() > 0

        d = c.discourse_sound_file("acoustic_corpus")
        assert os.path.exists(d["consonant_file_path"])


def test_remove_discourse(graph_db):
    with CorpusContext("load_remove_test", **graph_db) as c:
        c.remove_discourse("mfa_test")

        q = c.query_graph(c.word).filter(c.word.label == "JURASSIC")
        assert q.count() == 0
        q = c.query_graph(c.phone).filter(c.phone.label == "AE")
        assert q.count() == 0
        q = c.query_lexicon(c.syllable).filter(c.syllable.label == "JH.ER")
        assert q.count() == 0

        q = c.query_lexicon(c.lexicon_word).filter(c.lexicon_word.label == "JURASSIC")
        assert q.count() == 0
        q = c.query_lexicon(c.lexicon_phone).filter(c.lexicon_phone.label == "AE")
        assert q.count() == 0
        q = c.query_lexicon(c.lexicon_phone).filter(c.lexicon_phone.label == "ae")
        assert q.count() > 0
        q = c.query_lexicon(c.lexicon_syllable).filter(c.lexicon_syllable.label == "JH.ER")
        assert q.count() == 0

        q = c.query_discourses().filter(c.discourse.name == "mfa_test")
        assert q.count() == 0
        q = c.query_speakers().filter(c.speaker.name == "mfa")
        assert q.count() == 0

        d = c.discourse_sound_file("acoustic_corpus")
        assert os.path.exists(d["consonant_file_path"])

        c.remove_discourse("acoustic_corpus")
        assert not os.path.exists(d["consonant_file_path"])
