import pytest

from polyglotdb import CorpusContext

from polyglotdb.graph.models import LinguisticAnnotation, SubAnnotation

from polyglotdb.exceptions import SubannotationError

def test_models(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        q = c.query_graph(c.phone).order_by(c.phone.begin)
        q = q.columns(c.phone.id.column_name('id'))

        results = q.all()
        id = results[0]['id']

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == '<SIL>')

        assert(model.following.label == 'dh')

        assert(model.following.following.label == 'ih')
        assert(model.previous is None)

def test_type_properties(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        c.reset_pauses()
        q = c.query_graph(c.word).order_by(c.word.begin)
        q = q.columns(c.word.id.column_name('id'))

        results = q.all()
        id = results[1]['id']

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == 'this')
        assert(model.transcription == 'dh.ih.s')

def test_hierarchical(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        q = c.query_graph(c.word).order_by(c.word.begin)
        q = q.columns(c.word.id.column_name('id'))

        results = q.all()
        id = results[1]['id']

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == 'this')
        assert([x.label for x in model.phone] == ['dh','ih','s'])

        q = c.query_graph(c.phone).order_by(c.phone.begin)
        q = q.columns(c.phone.id.column_name('id'))

        results = q.all()
        id = results[1]['id']

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == 'dh')
        assert(model.word.label == 'this')

def test_subannotations(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).columns(c.phone.voicing_during_closure.id.column_name('voicing_ids'))
        res = q.all()
        for x in res:
            if len(x['voicing_ids']) > 0:
                id = x['voicing_ids'][0]
                break
        model = SubAnnotation(c)
        model.load(id)
        assert(model._type == 'voicing_during_closure')
        assert(round(model.duration, 2) == 0.03)

def test_add_subannotation(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).order_by(c.phone.id)
        q = q.columns(c.phone.id.column_name('id'))
        res = q.all()
        id = res[0]['id']
        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.voicing_during_closure == [])

        model.add_subannotation('voicing_during_closure', begin = 100, end = 101)
        model.save()
        print(model._subannotations)
        print(model.voicing_during_closure)
        assert(model.voicing_during_closure[0].begin == 100)
        id = model.voicing_during_closure[0].id

        submodel = SubAnnotation(c)
        submodel.load(id)

        submodel.update_properties(begin = 99)

        submodel.save()

        q = c.query_graph(c.phone).order_by(c.phone.id)
        res = q.all()
        id = res[0]['id']
        model = LinguisticAnnotation(c)
        model.load(id)

        assert(model.voicing_during_closure[0].begin == 99)

def test_preload(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        q = c.query_graph(c.phone)
        q = q.order_by(c.phone.begin).preload(c.phone.word)
        print(q.cypher())
        results = q.all()

        for r in results:
            assert('word' in r._supers)
            assert(r._supers['word'] is not None)

        q = c.query_graph(c.word)
        q = q.order_by(c.word.begin).preload(c.word.phone)
        print(q.cypher())
        results = q.all()

        for r in results:
            assert('phone' in r._subs)
            assert(r._subs['phone'] is not None)

def test_preload_sub(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone)
        q = q.order_by(c.phone.begin).preload(c.phone.voicing_during_closure)
        print(q.cypher())
        results = q.all()

        for r in results:
            if (r.label == 'g' and r.begin == 2.2) or r.begin == 0:
                assert('voicing_during_closure' in r._subannotations)
                assert(r._subannotations['voicing_during_closure'] is not None)
            else:
                assert('voicing_during_closure' not in r._subannotations)

        q = c.query_graph(c.word)
        q = q.order_by(c.word.begin).preload(
                    c.word.phone)
        print(q.cypher())
        results = q.all()
        print(len(results))
        for r in results:
            assert('phone' in r._subs)
            assert(r._subs['phone'] is not None)
            for e in r._subs['phone']:
                if e.label == 'k' and e.begin == 0:
                    assert('burst' in e._subannotations)
                    assert(e._subannotations['burst'][0].begin == 0)

        assert(any('voicing_during_closure' in e._subannotations for r in results for e in r._subs['phone'] ))
        assert(any(e._subannotations['voicing_during_closure'] is not None for r in results for e in r._subs['phone']))

def test_delete(subannotation_config):
    with CorpusContext(subannotation_config) as c:

        q = c.query_graph(c.phone).order_by(c.phone.id)
        res = q.all()
        id = res[0].id
        model = LinguisticAnnotation(c)
        model.load(id)

        assert(model.voicing_during_closure[0].begin == 99)

        model.delete_subannotation(model.voicing_during_closure[0])

        q = c.query_graph(c.phone).order_by(c.phone.id)
        res = q.all()
        id = res[0].id
        model = LinguisticAnnotation(c)
        model.load(id)

        assert(model.voicing_during_closure == [])
