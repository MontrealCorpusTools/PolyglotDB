import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import ParseError
from polyglotdb.io import inspect_maus


def test_load_aus(maus_test_dir, graph_db):
    with CorpusContext("test_mfa", **graph_db) as c:
        c.reset()
        testFilePath = os.path.join(maus_test_dir, "maus_test.TextGrid")
        parser = inspect_maus(testFilePath)
        print(parser.speaker_parser)
        c.load(parser, testFilePath)
        assert c.hierarchy.has_type_property("word", "transcription")

        q = c.query_graph(c.word).filter(c.word.label == "JURASSIC")
        print(q)
        print(q.all())
        q = q.filter(c.word.speaker.name == "maus_test")
        print(q.all())
        q = q.order_by(c.word.begin)
        print(q.all())
        q = q.columns(c.word.label)
        print(q.all())
        results = q.all()
        assert len(results) == 1

        c.encode_pauses("<SIL>")

        c.encode_utterances(min_pause_length=0)

        q = c.query_graph(c.word).filter(c.word.label == "PLANET")
        q = q.filter(c.word.speaker.name == "maus_test")
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name("following"))
        results = q.all()
        assert len(results) == 1
        assert results[0]["following"] == "JURASSIC"

        q = c.query_speakers().filter(c.speaker.name == "maus_test")
        q = q.columns(c.speaker.discourses.name.column_name("discourses"))

        s = q.get()

        assert len(s["discourses"]) == 1
        assert s["discourses"] == ["maus_test"]


def test_mismatch_parser(timit_test_dir, graph_db):
    with CorpusContext("test_mismatch", **graph_db) as c:
        c.reset()
        parser = inspect_maus(timit_test_dir)
        with pytest.raises(ParseError):
            c.load(parser, timit_test_dir)
