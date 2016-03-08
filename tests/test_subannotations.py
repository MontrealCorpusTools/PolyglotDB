import os
import pytest

from polyglotdb.corpus import CorpusContext
from polyglotdb.graph.func import Sum

from polyglotdb.exceptions import SubannotationError

def test_basic(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).filter(c.phone.label == 'g')
        q = q.columns(c.phone.label.column_name('label'))
        q = q.columns(c.phone.voicing_during_closure.duration.column_name('voicing_during_closure'))
        q = q.order_by(c.phone.begin)
        res = q.all()
        assert(res[0].label == 'g')
        assert([round(x, 2) for x in res[0].voicing_during_closure] == [0.03, 0.01])
        q = c.query_graph(c.phone).filter(c.phone.label == 'g')
        q = q.order_by(c.phone.begin)
        q = q.columns(c.phone.label.column_name('label'),
                    Sum(c.phone.voicing_during_closure.duration).column_name('voicing_during_closure'))

        print(q.cypher())
        res = q.all()
        print(res)
        print(res[0])
        assert(res[0].label == 'g')
        assert(round(res[0].voicing_during_closure, 2) == 0.04)

@pytest.mark.xfail
def test_filter(subannotation_config):
    with CorpusContext(subannotation_config) as c:

        q = c.query_graph(c.phone)
        q = q.filter(c.phone.burst.begin == 0)
        print(q.cypher())
        assert(q.all()[0].label == 'k')

def test_add_token_label(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).filter(c.phone.label == 'ae')
        q.set_token('ae', aeness = 'such ae')

        q = c.query_graph(c.phone).filter(c.phone.aeness == 'such ae')
        results = q.all()
        assert(len(results) > 0)
        assert(results[0].label == 'ae')

        q = c.query_graph(c.phone).filter(c.phone.aeness == None)
        print(q.cypher())
        results = q.all()
        assert(len(results) > 0)
        assert(all(x.label != 'ae' for x in results))

        q = c.query_graph(c.phone).filter(c.phone.aeness == 'such ae')
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

