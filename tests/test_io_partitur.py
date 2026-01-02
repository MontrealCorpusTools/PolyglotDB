import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.io.inspect.partitur import inspect_partitur
from polyglotdb.io.parsers.partitur import PartiturParser


def test_load_partitur(partitur_test_dir, graph_db):
    with CorpusContext("test_partitur", **graph_db) as c:
        c.reset()
        parser = inspect_partitur(partitur_test_dir)
        c.load(parser, partitur_test_dir)

        assert c.hierarchy.has_type_property("word", "transcription")

        q = c.query_graph(c.word).filter(c.word.label == "möchte")
        q = q.filter(c.word.speaker.name == "alz")
        results = q.all()
        assert len(results) == 1

        c.encode_pauses("<p:>")

        c.encode_utterances(min_pause_length=0)

        q = c.query_graph(c.utterance)
        results = q.all()
        assert len(results) == 1

        q = c.query_graph(c.word).filter(c.word.label == "wer")
        q = q.filter(c.word.speaker.name == "alz")
        q = q.order_by(c.word.begin)
        q = q.columns(
            c.word.label.column_name("label"),
            c.word.following.label.column_name("following"),
        )
        results = q.all()
        assert len(results) == 1

        assert results[0]["following"] == "möchte"

        q = c.query_speakers().filter(c.speaker.name == "alz")
        q = q.columns(c.speaker.discourses.name.column_name("discourses"))

        s = q.get()

        assert len(s["discourses"]) == 1
        assert s["discourses"] == ["partitur_test"]
