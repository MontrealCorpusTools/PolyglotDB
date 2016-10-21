
import pytest

from polyglotdb import CorpusContext

from polyglotdb.syllabification.probabilistic import split_ons_coda_prob, split_nonsyllabic_prob, norm_count_dict
from polyglotdb.syllabification.maxonset import split_ons_coda_maxonset, split_nonsyllabic_maxonset
from polyglotdb.syllabification.main import syllabify

def test_find_onsets(timed_config):
    syllabics = ['ae','aa','uw','ay','eh']
    expected_onsets = set([('k',), tuple(), ('d',), ('t',),('g',)])
    expected_freqs = {('k',): 2, tuple():3, ('d',):1, ('t',):1,('g',):1}
    with CorpusContext(timed_config) as c:
        c.encode_syllabic_segments(syllabics)
        onsets = c.find_onsets()
        assert(set(onsets.keys()) == expected_onsets)
        assert(onsets == expected_freqs)

def test_find_codas(timed_config):
    expected_codas = set([('t','s'), ('r',), ('t',), ('g','z'), tuple(), ('s',)])
    expected_freqs = {('t','s'): 1, tuple():2, ('r',):2, ('t',):1,('g','z'):1, ('s',):1}
    with CorpusContext(timed_config) as c:
        codas = c.find_codas()
        assert(set(codas.keys()) == expected_codas)
        assert(codas == expected_freqs)
@pytest.mark.xfail
def test_probabilistic_syllabification(acoustic_config, timed_config):
    with CorpusContext(timed_config) as c:
        onsets = norm_count_dict(c.find_onsets())
        codas = norm_count_dict(c.find_codas())
    print(onsets)
    print(codas)
    expected = [(['z','g'], 1), (['g','z'], 2), (['t', 's', 'k'], 2), (['t', 'd'], 1)]
    for s, e in expected:
        result = split_ons_coda_prob(s, onsets, codas)
        print(s, e, result)
        assert(e == result)

    with CorpusContext(acoustic_config) as c:
        onsets = norm_count_dict(c.find_onsets())
        codas = norm_count_dict(c.find_codas())
    #nonsyllabic
    expected = [(['d','g','z'], 2), (['sh'], 0)]
    for s, e in expected:
        result = split_nonsyllabic_prob(s, onsets, codas)
        print(s, e, result)
        assert(e == result)

def test_maxonset_syllabification(acoustic_config, timed_config):
    with CorpusContext(timed_config) as c:
        onsets = set(c.find_onsets().keys())

    print(onsets)
    expected = [(['z','g'], 1), (['g','z'], 2), (['t', 's', 'k'], 2), (['t', 'd'], 1)]
    for s, e in expected:
        result = split_ons_coda_maxonset(s, onsets)
        print(s, e, result)
        assert(e == result)

    #nonsyllabic
    expected = [(['d','g','z'], 1), (['sh'], 0)]
    for s, e in expected:
        result = split_nonsyllabic_maxonset(s, onsets)
        print(s, e, result)
        assert(e == result)


def test_syllabify(acoustic_config, timed_config):
    expected = {('n','ay','iy','v'):[{'label':'n.ay'}, {'label':'iy.v'}],
                ('l','ow','w','er'):[{'label':'l.ow'}, {'label':'w.er'}]}
    s = ['ay','iy', 'ow', 'er']
    o = [('n',),('v',), ('w',), ('l',)]
    c = [('v',)]
    for k,v in expected.items():
        test = syllabify(k,s,o,c,'maxonset')
        assert(len(test) == len(v))
        for i, x in enumerate(v):
            for k2, v2 in x.items():
                assert(v2 == test[i][k2])

def test_encode_syllables_acoustic(acoustic_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(acoustic_config) as c:
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables()

        q = c.query_graph(c.phone).filter(c.phone.label == 'dh')
        q = q.filter(c.phone.begin == c.phone.syllable.begin)
        q = q.order_by(c.phone.begin)
        q = q.columns(c.phone.label, c.phone.begin)

        results = q .all()
        assert(len(results) == 5)

        #c.reset_syllables()
