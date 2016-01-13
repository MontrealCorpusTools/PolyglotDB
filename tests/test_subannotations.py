import os
import pytest

from polyglotdb.corpus import CorpusContext
from polyglotdb.graph.func import Sum

def test_basic(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).columns(c.phone.voicing_during_closure.duration.column_name('voicing_during_closure'))
        res = q.all()
        assert(res[0].label == 'g')
        assert([round(x, 2) for x in res[0].voicing_during_closure] == [0.03, 0.01])
        q = c.query_graph(c.phone)
        res = q.aggregate(Sum(c.phone.voicing_during_closure.duration).column_name('voicing_during_closure'))
        print(res)
        print(res[0])
        assert(res[0].label == 'g')
        assert(round(res[0].voicing_during_closure, 2) == 0.04)

def test_add_token_label(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).filter(c.phone.label == 'ae')
        q.set_token('ae', aeness = 'such ae')

        q = c.query_graph(c.phone).filter(c.phone.aeness == 'such ae')
        results = q.all()
        assert(len(results) > 0)
        assert(results[0].label == 'ae')

        q.set_token(aeness = None)

        q = c.query_graph(c.phone).filter(c.phone.aeness == 'such ae')
        results = q.all()
        assert(len(results) == 0)

        q = c.query_graph(c.phone).filter(c.phone.label == 't')
        q.set_type('t', tness = 'such t')

        q = c.query_graph(c.phone.subset_type('t'))
        results = q.all()
        assert(len(results) > 0)
        assert(results[0].label == 't')


def test_delete(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).filter(c.phone.label == 'ae')
        q.delete()

        q = c.query_graph(c.phone).filter(c.phone.label == 'ae')
        results = q.all()
        assert(len(results) == 0)
