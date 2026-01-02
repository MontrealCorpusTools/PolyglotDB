import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import ParseError
from polyglotdb.io import inspect_mfa


def test_load_mfa(mfa_test_dir, graph_db):
    with CorpusContext("test_mfa", **graph_db) as c:
        c.reset()
        testFilePath = os.path.join(mfa_test_dir, "mfa_test.TextGrid")
        parser = inspect_mfa(testFilePath)
        print(parser.speaker_parser)
        c.load(parser, testFilePath)
        assert c.hierarchy.has_type_property("word", "transcription")

        q = c.query_graph(c.word).filter(c.word.label == "JURASSIC")
        print(q)
        print(q.all())
        q = q.filter(c.word.speaker.name == "mfa")
        # print(c.word.speaker.name)
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
        q = q.filter(c.word.speaker.name == "mfa")
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name("following"))
        results = q.all()
        assert len(results) == 1
        assert results[0]["following"] == "JURASSIC"

        q = c.query_speakers().filter(c.speaker.name == "mfa")
        q = q.columns(c.speaker.discourses.name.column_name("discourses"))

        s = q.get()

        assert len(s["discourses"]) == 1
        assert s["discourses"] == ["mfa_test"]


def test_mismatch_parser(timit_test_dir, graph_db):
    with CorpusContext("test_mismatch", **graph_db) as c:
        c.reset()
        parser = inspect_mfa(timit_test_dir)
        with pytest.raises(ParseError):
            c.load(parser, timit_test_dir)


def test_two_format_parsing(mfa_test_dir, graph_db):
    # for file in os.listdir(os.path.abspath(mfa_test_dir)):
    #    if file.endswith("yes.TextGrid") or file.endswith("no.TextGrid"):
    #        path = os.path.join(mfa_test_dir, file)
    # parser = MfaParser("a", "b")
    #        curTg = TextGrid()
    #        curTg.read(path)
    # value = parser._is_valid(curTg)

    # if file.endswith("yes.TextGrid"):
    #    assert True
    # elif file.endswith("no.TextGrid"):
    #    assert False
    valid_dir = os.path.join(mfa_test_dir, "valid")
    invalid_dir = os.path.join(mfa_test_dir, "invalid")

    # Check that valids load
    with CorpusContext("mfa_valid", **graph_db) as c:
        c.reset()
        parser = inspect_mfa(valid_dir)
        c.load(parser, valid_dir)

    # Check that invalids don't
    with CorpusContext("mfa_invalid", **graph_db) as c:
        c.reset()
        parser = inspect_mfa(invalid_dir)
        with pytest.raises(ParseError):
            c.load(parser, invalid_dir)
