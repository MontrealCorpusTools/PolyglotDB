import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import GraphQueryError, TextGridError
from polyglotdb.io import inspect_fave


def test_load_fave(fave_test_dir, graph_db):
    with CorpusContext("test_fave", **graph_db) as c:
        c.reset()
        parser = inspect_fave(fave_test_dir)
        c.load(parser, fave_test_dir)
        assert c.hierarchy.has_type_property("word", "transcription")

        q = c.query_graph(c.word).filter(c.word.label == "JURASSIC")
        q = q.filter(c.word.speaker.name == "Gary Salvi")
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label)
        print(q.cypher())
        results = q.all()
        assert len(results) == 1

        q = c.query_graph(c.word).filter(c.word.label == "JURASSIC")
        q = q.filter(c.word.speaker.name == "Interviewer")
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label)
        print(q.cypher())
        results = q.all()
        assert len(results) == 0

        c.encode_pauses("<SIL>")

        c.encode_utterances(min_pause_length=0)

        q = c.query_graph(c.word).filter(c.word.label == "PLANET")
        q = q.filter(c.word.speaker.name == "Gary Salvi")
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name("following"))
        print(q.cypher())
        results = q.all()
        assert len(results) == 1
        assert results[0]["following"] == "JURASSIC"

        q = c.query_graph(c.word).filter(c.word.label == "MURDER")
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name("following"))
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[0]["following"] == "KNOW"

        q = c.query_speakers().filter(c.speaker.name == "Interviewer")
        q = q.columns(c.speaker.discourses.name.column_name("discourses"))

        interviewer = q.get()

        assert len(interviewer["discourses"]) == 2
        assert sorted(interviewer["discourses"]) == ["fave_test", "fave_test2"]

        q = c.query_speakers().filter(c.speaker.name == "Gary Salvi")
        q = q.columns(c.speaker.discourses.name.column_name("discourses"))

        s = q.get()

        assert len(s["discourses"]) == 1
        assert s["discourses"] == ["fave_test"]


def test_load_fave_stereo(fave_test_dir, graph_db):
    with CorpusContext("test_stereo", **graph_db) as c:
        c.reset()
        parser = inspect_fave(fave_test_dir)
        c.load(parser, fave_test_dir)

        q = c.query_speakers().filter(c.speaker.name == "Speaker 1")
        q = q.columns(
            c.speaker.discourses.name.column_name("discourses"),
            c.speaker.discourses.channel.column_name("channels"),
        )

        s = q.get()

        assert len(s["channels"]) == 1
        assert s["channels"] == [0]

        q = c.query_speakers().filter(c.speaker.name == "Speaker's+2?&!#$%()*:;<=>@__")
        q = q.columns(
            c.speaker.discourses.name.column_name("discourses"),
            c.speaker.discourses.channel.column_name("channels"),
        )

        s = q.get()

        assert len(s["channels"]) == 1
        assert s["channels"] == [1]
