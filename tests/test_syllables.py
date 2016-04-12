
import pytest

from polyglotdb import CorpusContext

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

def test_encode_syllables_acoustic(acoustic_config):
    pass
