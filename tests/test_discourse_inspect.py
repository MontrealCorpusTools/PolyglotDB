import pytest

from polyglotdb import CorpusContext

@pytest.mark.xfail #Outdated functionality
def test_inspect_discourse(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        d = g.inspect_discourse('acoustic_corpus', 0, 5)

        assert (len(d) == 1)

        d.update_times(1, 2)

        assert (len(d) == 1)

        d.update_times(0, 9)

        assert (len(d) == 2)
