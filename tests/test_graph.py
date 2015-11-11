import os
import pytest

from polyglotdb.corpus import CorpusContext
from polyglotdb.graph.func import Count

def test_basic_query(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        print(q.cypher())
        assert(all(x.label == 'are' for x in q.all()))

@pytest.mark.xfail
def test_aggregate_element(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter(Count(g.word.label) >= 2).columns(g.word.label.column_name('word_label'))
        print(q.cypher())
        results = q.all()
        assert(len(results) == 2)
        assert(all(x.word_label == 'are' for x in results))

def test_strings(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q .columns(g.word.phone.label.column_name('phones'))
        print(q.cypher())
        results = q.all()
        assert(all(x.label == 'are' for x in results))
        assert(all(x.phones == ['aa','r'] for x in results))

def test_columns(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.word.label.column_name('word_label'), g.line.id)
        print(q.cypher())
        results = q.all()
        assert(all(x.word_label in ['are', 'dogs'] for x in results))

def test_discourse_query(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).columns(g.word.discourse.column_name('discourse'))
        print(q.cypher())
        assert(all(x.discourse == 'test' for x in q.all()))


def test_order_by(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are').order_by(g.word.begin.column_name('begin'))#.times('begin','end')
        prev = 0
        print(q.cypher())
        print(q.all())
        for x in q.all():
            assert(x.begin > prev)
            prev = x.begin

def test_basic_discourses_prop(timed_config):
    with CorpusContext(timed_config) as g:
        assert(g.discourses == ['test'])

def test_query_previous(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.previous.label == 'cats')
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_following(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.following.label == 'too')
        print(q.cypher())
        print(list(q.all()))
        assert(len(list(q.all())) == 1)

def test_query_time(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.begin > 2)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.begin < 2)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_contains(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).filter_contains(g.phone.label == 'aa')
        print(q.cypher())
        assert(len(list(q.all())) == 3)

def test_query_contained_by(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter_contained_by(g.word.label == 'dogs')
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_columns_contained(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.word.label)
        print(q.cypher())
        assert(len(list(q.all())) == 3)

def test_query_left_aligned_line(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_left_aligned(g.line)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_previous_left_aligned_line(untimed_config, timed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'ae')
        q = q.filter(g.phone.previous.begin == g.line.begin)
        print(q.cypher())
        assert(q.count() == 1)
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'ae')
        q = q.filter(g.phone.previous.begin == g.line.begin)
        print(q.cypher())
        assert(q.count() == 1)

def test_query_phone_in_line_initial_word(untimed_config):
    with CorpusContext(untimed_config) as g:
        word_q = g.query_graph(g.word).filter_left_aligned(g.line)
        assert(len(list(word_q.all())) == 3)
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter_contained_by(g.word.id.in_(word_q))
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_word_in(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_contained_by(g.word.label.in_(['cats','dogs','cute']))
        print(q.cypher())
        assert(len(list(q.all())) == 2)

def test_query_coda_phone(syllable_morpheme_config):
    with CorpusContext(syllable_morpheme_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_right_aligned(g.syllable)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.end == g.syllable.end)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_not_right_aligned(g.syllable)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.end != g.syllable.end)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

def test_query_onset_phone(syllable_morpheme_config):
    with CorpusContext(syllable_morpheme_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_left_aligned(g.syllable)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.begin == g.syllable.begin)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_not_left_aligned(g.syllable)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.begin != g.syllable.begin)
        print(q.cypher())
        assert(len(list(q.all())) == 1)

@pytest.mark.xfail
def test_query_frequency(untimed_config):
    with CorpusContext(untimed_config) as g:
        q = g.query_graph(g.word).filter(g.word.frequency > 1)
        print(q.cypher())
    assert(False)

def test_regex_query(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.regex('a.'))
        print(q.cypher())
        assert(q.count() == 5)

