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
