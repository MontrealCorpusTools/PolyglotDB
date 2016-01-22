import os
import pytest

from polyglotdb.corpus import CorpusContext

def test_position_query(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.columns(g.phone.word.phone.position.column_name('position'))
        q = q.order_by(g.phone.word.begin)
        print(q.cypher())
        results = q.all()
        expected = [1,1]
        assert(len(results) == len(expected))
        for i in range(len(expected)):
            assert(results[i].position == expected[i])

def test_initial_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'this')
        q = q.columns(g.word.following.phone.initial.label.column_name('initial_following_phone'),
                    g.word.following.phone.initial.duration.column_name('initial_following_phone_duration'),
                    g.word.following.phone.initial.begin.column_name('begin'),
                    g.word.following.phone.initial.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].initial_following_phone == 'ih')
        assert(abs(results[0].initial_following_phone_duration - 0.062353) < 0.001)
        assert(abs(results[0].begin - 1.203942) < 0.001)
        assert(abs(results[0].end - 1.266295) < 0.001)

def test_final_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'is')
        q = q.columns(g.word.previous.phone.final.label.column_name('final_previous_phone'),
                    g.word.previous.phone.final.duration.column_name('final_previous_phone_duration'),
                    g.word.previous.phone.final.begin.column_name('begin'),
                    g.word.previous.phone.final.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].final_previous_phone == 's')
        assert(abs(results[0].final_previous_phone_duration - 0.079107) < 0.001)
        assert(abs(results[0].begin - 1.124835) < 0.001)
        assert(abs(results[0].end - 1.203942) < 0.001)

def test_penult_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'is')
        q = q.columns(g.word.previous.phone.penultimate.label.column_name('phone'),
                    g.word.previous.phone.penultimate.duration.column_name('duration'),
                    g.word.previous.phone.penultimate.begin.column_name('begin'),
                    g.word.previous.phone.penultimate.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].phone == 'ih')
        assert(abs(results[0].duration - 0.042712) < 0.001)
        assert(abs(results[0].begin - 1.082123) < 0.001)
        assert(abs(results[0].end - 1.124835) < 0.001)

        q = g.query_graph(g.word).filter(g.word.label == 'is')
        q = q.columns(g.word.previous.phone.antepenultimate.label.column_name('phone'),
                    g.word.previous.phone.antepenultimate.duration.column_name('duration'),
                    g.word.previous.phone.antepenultimate.begin.column_name('begin'),
                    g.word.previous.phone.antepenultimate.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].phone == 'dh')
        assert(abs(results[0].duration - 0.022900) < 0.001)
        assert(abs(results[0].begin - 1.059223) < 0.001)
        assert(abs(results[0].end - 1.082123) < 0.001)
