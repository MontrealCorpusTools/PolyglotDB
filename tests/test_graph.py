import os
import pytest

from polyglotdb.corpus import CorpusContext

def test_basic_query(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        assert(all(x.r_word['label'] == 'are' for x in q.all()))

def test_order_by(graph_db):
    with CorpusContext(corpus_name = 'timed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are').order_by(g.word.begin.column_name('begin')).times('begin','end')
        prev = 0
        for x in q.all():
            assert(x.begin > prev)
            prev = x.begin

def test_query_previous(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.previous.label == 'cats')
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_following(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.following.label == 'too')
        print(q.cypher())
        print(list(q.all()))
        assert(len(list(q.all())) == 1)

def test_query_time(graph_db):
    with CorpusContext(corpus_name = 'timed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.begin > 2)
        print(q.cypher())
        assert(len(list(q.all())) == 1)
    with CorpusContext(corpus_name = 'timed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.begin < 2)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_contains(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.word).filter_contains(g.phone.label == 'aa')
        print(q.cypher())
        print(list(q.all()))
        assert(len(list(q.all())) == 3)

def test_query_contained_by(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter_contained_by(g.word.label == 'dogs')
        assert(len(list(q.all())) == 1)

def test_query_left_aligned_line(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_left_aligned(g.line)
        assert(len(list(q.all())) == 1)

def test_query_phone_in_line_initial_word(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        word_q = g.query_graph(g.word).filter_left_aligned(g.line)
        assert(len(list(word_q.all())) == 3)
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter_contained_by(g.word.id.in_(word_q))
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_word_in(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_contained_by(g.word.label.in_(['cats','dogs','cute']))
        print(q.cypher())
        assert(len(list(q.all())) == 2)

def test_query_coda_phone(graph_db):
    with CorpusContext(corpus_name = 'syllable_morpheme', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_right_aligned(g.syllable)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

@pytest.mark.xfail
def test_query_frequency(graph_db):
    with CorpusContext(corpus_name = 'untimed', **graph_db) as g:
        q = g.query_graph(g.word).filter(g.word.frequency > 1)
    assert(False)

def test_query_aggregate_count(graph_db):
    with CorpusContext(corpus_name = 'timed', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa').count()
        assert(q == 3)


