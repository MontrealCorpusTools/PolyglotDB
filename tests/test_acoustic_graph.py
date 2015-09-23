
import os
import pytest

from polyglotdb.corpus import CorpusContext
from polyglotdb.graph.func import Average, Count

def test_query_duration(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa').order_by(g.phone.begin.column_name('begin')).duration()
        print(q.cypher())
        results = q.all()
        assert(len(results) == 3)
        assert(abs(results[0].begin - 2.704) < 0.001)
        assert(abs(results[0].duration - 0.078) < 0.001)

        assert(abs(results[1].begin - 9.320) < 0.001)
        assert(abs(results[1].duration - 0.122) < 0.001)

        assert(abs(results[2].begin - 24.560) < 0.001)
        assert(abs(results[2].duration - 0.039) < 0.001)

def test_query_duration_aggregate_average(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        results = q.aggregate(Average(g.phone.duration))
        print(results)
        assert(abs(results[0].average_duration - 0.08) < 0.001)

def test_query_count_group_by(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa','ae']))
        results = q.group_by(g.phone.label.column_name('label')).aggregate(Count())
        assert(len(results) == 2)
        print(results)
        assert(results[0].label == 'aa')
        assert(results[0].count_all == 3)

        assert(results[1].label == 'ae')
        assert(results[1].count_all == 7)

def test_query_duration_aggregate_average_group_by(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa','ae']))
        results = q.group_by(g.phone.label.column_name('label')).aggregate(Average(g.phone.duration))

        assert(len(results) == 2)
        assert(results[0].label == 'aa')
        assert(abs(results[0].average_duration - 0.08) < 0.001)

        assert(results[1].label == 'ae')
        assert(abs(results[1].average_duration - 0.193) < 0.001)

@pytest.mark.xfail
def test_query_pitch(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa').pitch('praat')

    assert(False)

@pytest.mark.xfail
def test_query_formants(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa').formants('praat')

    assert(False)

@pytest.mark.xfail
def test_query_formants_aggregate_group_by(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa','ae']))
        q = q.group_by(Annotation.label).formants('praat').average()

    assert(False)

@pytest.mark.xfail
def test_query_speaking_rate(graph_db):
    with CorpusContext(corpus_name = 'acoustic', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.preceding_speaking_rate().following_speaking_rate()

    assert(False)
