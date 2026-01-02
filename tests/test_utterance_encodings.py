import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import AnnotationAttributeError


def test_encode_positions(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.encode_utterance_position()

        q = g.query_graph(g.phone).columns(
            g.phone.word.label.column_name("label"),
            g.phone.word.position_in_utterance.column_name("pos"),
            g.phone.utterance.begin.column_name("begin"),
            g.phone.syllable.word.utterance.end.column_name("end"),
        )
        q = q.order_by(g.phone.word.begin)
        results = q.all()
        assert len(results) > 0
        assert results[0]["label"] == "this"
        assert results[0]["pos"] == 1

        q = g.query_graph(g.word).columns(
            g.word.label.column_name("label"),
            g.word.position_in_utterance.column_name("pos"),
        )
        q = q.order_by(g.word.begin)
        results = q.all()
        assert results[0]["label"] == "this"
        assert results[0]["pos"] == 1

        q = g.query_graph(g.word)
        q = q.filter(g.word.begin == g.utterance.begin)
        q = q.columns(
            g.word.label.column_name("label"),
            g.word.position_in_utterance.column_name("pos"),
        )
        q = q.order_by(g.word.begin)
        results = q.all()
        assert all(x["pos"] == 1 for x in results)

        print("resetting utterance position")
        g.reset_utterance_position()

        q = g.query_graph(g.word)
        with pytest.raises(AnnotationAttributeError):
            g.word.position_in_utterance == 0


def test_encode_speech_rate(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        label = "somethingsomething"

        g.encode_class(["dh"], label)

        g.encode_speech_rate(label)

        q = g.query_graph(g.utterance)
        q = q.columns(g.utterance.speech_rate.column_name("speech_rate"))
        q = q.order_by(g.utterance.begin)
        results = q.all()

        assert round(results[0]["speech_rate"], 5) == round(4 / (7.541484 - 1.059223), 5)

        print("resetting speech rate")
        g.reset_speech_rate()

        q = g.query_graph(g.utterance)
        with pytest.raises(AnnotationAttributeError):
            g.utterance.speech_rate == 0
