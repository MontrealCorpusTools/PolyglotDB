
import pytest

from polyglotdb.corpus import CorpusContext

def test_generate_hierarchy(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        h = c.generate_hierarchy()
        assert(h._data == c.hierarchy._data)

def test_generate_hierarchy_subannotations(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        h = c.generate_hierarchy()
        assert(h._data == c.hierarchy._data)
        assert(h.subannotations['phone'] == c.hierarchy.subannotations['phone'])
