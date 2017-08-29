import pytest

from polyglotdb import CorpusContext
from polyglotdb.query.base.func import Count
from polyglotdb.query.base.complex import or_, and_
from polyglotdb.utils import get_corpora_list


def test_basic_query(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        print(g.word.label == 'are')
        print(q.cypher())
        assert (all(x['label'] == 'are' for x in q.all()))
    assert ('timed' in get_corpora_list(timed_config))


@pytest.mark.xfail
def test_aggregate_element(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter(Count(g.word.label) >= 2).columns(g.word.label.column_name('word_label'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 2)
        assert (all(x['word_label'] == 'are' for x in results))


def test_strings(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.columns(g.word.label.column_name('label'),
                      g.word.phone.label.column_name('phones'))
        print(q.cypher())
        results = q.all()

        assert (all(x['label'] == 'are' for x in results))
        assert (all(x['phones'] == ['aa', 'r'] for x in results))


def test_columns(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.word.label.column_name('word_label'), g.phone.line.id)
        print(q.cypher())
        results = q.all()
        assert (all(x['word_label'] in ['are', 'dogs'] for x in results))


def test_discourse_query(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).columns(g.word.discourse.name.column_name('discourse'))
        print(q.cypher())
        assert (all(x['discourse'] == 'test_timed' for x in q.all()))

        q = g.query_graph(g.word).filter(g.word.discourse.name == 'test')
        q = q.columns(g.word.discourse.name.column_name('discourse'))
        print(q.cypher())
        assert (all(x['discourse'] == 'test_timed' for x in q.all()))


def test_order_by(timed_config):
    with CorpusContext(timed_config) as g:
        print(g.hierarchy.type_properties)
        print(g.hierarchy.token_properties)
        q = g.query_graph(g.word).filter(g.word.label == 'are').order_by(
            g.word.begin.column_name('begin'))
        prev = 0
        print(q.cypher())
        print(q.all())
        for x in q.all():
            print(x['begin'])
            assert (x['begin'] > prev)
            prev = x['begin']
    assert ('timed' in get_corpora_list(timed_config))


def test_basic_discourses_prop(timed_config):
    with CorpusContext(timed_config) as g:
        assert (g.discourses == ['test_timed'])


def test_query_previous(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.previous.label == 'cats')
        print(q.cypher())
        assert (len(list(q.all())) == 1)


def test_query_previous_previous(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'cute')
        q = q.filter(g.word.previous.label == 'are')
        q = q.filter(g.word.previous.previous.label == 'cats')
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)

        q = g.query_graph(g.word).filter(g.word.label == 'cute')
        q = q.columns(g.word.previous.label.column_name('previous_label'),
                      g.word.previous.previous.label.column_name('previous_previous_label'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['previous_label'] == 'are')
        assert (results[0]['previous_previous_label'] == 'cats')


def test_query_following(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.following.label == 'too')
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)


def test_query_following_following(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'cats')
        q = q.filter(g.word.following.label == 'are')
        q = q.filter(g.word.following.following.label == 'cute')
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)

        q = g.query_graph(g.word).filter(g.word.label == 'cats')
        q = q.columns(g.word.following.label.column_name('following_label'),
                      g.word.following.following.label.column_name('following_following_label'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['following_label'] == 'are')
        assert (results[0]['following_following_label'] == 'cute')


def test_query_time(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.begin > 2)
        print(q.cypher())
        assert (len(list(q.all())) == 1)

        q = g.query_graph(g.word).filter(g.word.label == 'are')
        q = q.filter(g.word.begin < 2)
        print(q.cypher())
        assert (len(list(q.all())) == 1)


def test_query_contains(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.phone.label == 'aa')
        print(q.cypher())
        assert (len(list(q.all())) == 3)


def test_query_contained_by(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter(g.phone.word.label == 'dogs')
        print(q.cypher())
        assert (len(list(q.all())) == 1)


def test_query_columns_contained(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.word.label)
        print(q.cypher())
        assert (len(list(q.all())) == 3)

        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.word.label, g.phone.word.line.label)
        print(q.cypher())
        assert (len(list(q.all())) == 3)

        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.word.label, g.phone.line.label)
        print(q.cypher())
        assert (len(list(q.all())) == 3)


def test_query_alignment(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_left_aligned(g.line)
        q = q.columns(g.phone.word.label)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['begin'] == 0)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.begin == g.phone.line.begin)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['begin'] == 0)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.begin != g.phone.line.begin)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['begin'] == 0.8)

        q = g.query_graph(g.phone).filter(g.phone.label == 's')
        q = q.filter_right_aligned(g.line)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['begin'] == 3.5)

        q = g.query_graph(g.phone).filter(g.phone.label == 's')
        q = q.filter(g.phone.end == g.phone.line.end)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['begin'] == 3.5)

        q = g.query_graph(g.phone).filter(g.phone.label == 's')
        q = q.filter(g.phone.end != g.phone.line.end)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['begin'] == 0.3)

        q = g.query_graph(g.phone).filter(g.phone.label == 's')
        q = q.filter(g.phone.following.following.end == g.phone.word.end)
        print(q.cypher())
        results = q.all()
        assert (len(results) == 0)

        q = g.query_graph(g.phone).filter(g.phone.following.label == 't')
        q = q.filter(g.phone.following.end == g.phone.word.end)
        print(q.cypher())
        results = q.all()
        assert (len(results) == 1)
        assert (results[0]['label'] == 'uw')


def test_query_previous_left_aligned_line(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'ae')
        q = q.filter(g.phone.previous.begin == g.line.begin)
        print(q.cypher())
        assert (q.count() == 1)


def test_query_phone_in_line_initial_word(timed_config):
    with CorpusContext(timed_config) as g:
        word_q = g.query_graph(g.word).filter_left_aligned(g.line)
        assert (len(list(word_q.all())) == 3)
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.filter(g.phone.word.id.in_(word_q))
        print(q.cypher())
        print(q.cypher_params())
        assert (len(list(q.all())) == 1)


def test_query_word_in(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.word.label.in_(['cats', 'dogs', 'cute']))
        print(q.cypher())
        assert (len(list(q.all())) == 2)


def test_query_coda_phone(syllable_morpheme_config):
    with CorpusContext(syllable_morpheme_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_right_aligned(g.syllable)
        print(q.cypher())
        assert (len(list(q.all())) == 2)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.end == g.syllable.end)
        print(q.cypher())
        assert (len(list(q.all())) == 2)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_not_right_aligned(g.syllable)
        print(q.cypher())
        assert (len(list(q.all())) == 0)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.end != g.syllable.end)
        print(q.cypher())
        assert (len(list(q.all())) == 0)
    assert ('syllable_morpheme' in get_corpora_list(syllable_morpheme_config))


def test_query_onset_phone(syllable_morpheme_config):
    with CorpusContext(syllable_morpheme_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_left_aligned(g.syllable)
        print(q.cypher())
        assert (len(list(q.all())) == 0)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.begin == g.syllable.begin)
        print(q.cypher())
        assert (len(list(q.all())) == 0)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter_not_left_aligned(g.syllable)
        print(q.cypher())
        assert (len(list(q.all())) == 2)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.filter(g.phone.begin != g.syllable.begin)
        print(q.cypher())
        assert (len(list(q.all())) == 2)


def test_complex_hierarchy(syllable_morpheme_config):
    with CorpusContext(syllable_morpheme_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.columns(g.phone.line.begin, g.phone.syllable.begin)
        results = q.all()
        print(q.cypher())
        assert (len(results) == 2)

        q = g.query_graph(g.phone).filter(g.phone.label == 'k')
        q = q.columns(g.phone.following_pause.label)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        results = q.all()
        print(q.cypher())
        assert (len(results) == 2)


@pytest.mark.xfail
def test_query_frequency(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.frequency > 1)
        print(q.cypher())
    assert (False)


def test_regex_query(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.regex('a.'))
        print(q.cypher())
        assert (q.count() == 5)


def test_query_duration(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.order_by(g.phone.begin)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'),
                      g.phone.duration.column_name('duration'))
        print(q.cypher())
        results = q.all()
        assert (len(results) == 3)
        assert (abs(results[0]['begin'] - 2.704) < 0.001)
        assert (abs(results[0]['duration'] - 0.078) < 0.001)

        assert (abs(results[1]['begin'] - 9.320) < 0.001)
        assert (abs(results[1]['duration'] - 0.122) < 0.001)

        assert (abs(results[2]['begin'] - 24.560) < 0.001)
        assert (abs(results[2]['duration'] - 0.039) < 0.001)
    assert ('acoustic' in get_corpora_list(acoustic_config))


def test_discourses_prop(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        assert (g.discourses == ['acoustic_corpus'])


def test_mirrored(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        vowels = ['ih']
        obstruents = ['s']
        q = g.query_graph(g.phone).filter(g.phone.label.in_(obstruents))
        q = q.filter(g.phone.previous.label.in_(vowels))
        q = q.filter(g.phone.following.label == g.phone.previous.label)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))
        print(q.cypher())

        results = q.all()
        print(results)
        assert (len(results) == 2)
        q = g.query_graph(g.phone).filter(g.phone.label.in_(obstruents))
        q = q.filter(g.phone.previous.label.in_(vowels))
        q = q.filter(g.phone.following.label == g.phone.previous.label)
        q = q.filter(g.phone.end == g.phone.word.end)
        # q = q.filter(g.phone.following.begin == g.phone.word.following.begin)
        q = q.columns(g.phone.begin.column_name('begin'),
                      g.phone.end.column_name('end'))

        print(q.cypher())

        results = q.all()
        print(results)
        assert (len(results) == 2)


def test_hierarchy_following(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.word.following.label)
        print(q.cypher())
        results = q.all()
        assert (len(results) == 3)


def test_or_clause(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(or_(g.word.label == 'are', and_(g.word.begin >= 3.3, g.word.end < 100)))
        q = q.order_by(g.word.begin)
        q = q.columns(g.word.label.column_name('label'), g.word.begin.column_name('begin'))
        print(q.cypher())
        results = q.all()

        q = g.query_graph(g.word).filter(g.word.label.in_(['are', 'guess']))
        q = q.order_by(g.word.begin)
        q = q.columns(g.word.label.column_name('label'), g.word.begin.column_name('begin'))
        expected = q.all()

        assert (len(expected) == len(results))

        for i, r in enumerate(results):
            assert (r['label'] == expected[i]['label'])
            assert (r['begin'] == expected[i]['begin'])

        q = g.query_graph(g.word).filter(or_(g.word.label == 'are', g.word.label == 'guess'))
        q = q.order_by(g.word.begin)
        q = q.columns(g.word.label.column_name('label'), g.word.begin.column_name('begin'))
        print(q.cypher())
        results = q.all()

        assert (len(expected) == len(results))

        for i, r in enumerate(results):
            assert (r['label'] == expected[i]['label'])
            assert (r['begin'] == expected[i]['begin'])


def test_precedes_clause(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'cute')
        a = q.all()[0]

        q = g.query_graph(g.word).filter(g.word.precedes(a))
        q = q.order_by(g.word.begin)
        print(q.cypher(), q.cypher_params())

        results = q.all()
        assert (len(results) == 2)
        assert (results[0].label == 'cats')
        assert (results[1].label == 'are')


def test_follows_clause(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'too')
        a = q.all()[0]

        q = g.query_graph(g.word).filter(g.word.follows(a))
        q = q.order_by(g.word.begin)
        print(q.cypher(), q.cypher_params())
        results = q.all()
        assert (len(results) == 2)
        assert (results[0].label == 'i')
        assert (results[1].label == 'guess')
