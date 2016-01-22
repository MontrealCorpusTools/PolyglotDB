import pytest

from polyglotdb.corpus import CorpusContext

from polyglotdb.graph.models import LinguisticAnnotation, SubAnnotation

def test_models(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        q = c.query_graph(c.phone).order_by(c.phone.begin)

        results = q.all()
        id = results[0].id

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == '<SIL>')

        assert(model.following.label == 'dh')

        assert(model.following.following.label == 'ih')
        assert(model.previous is None)

def test_type_properties(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        q = c.query_graph(c.word).order_by(c.word.begin)

        results = q.all()
        id = results[1].id

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == 'this')
        assert(model.transcription == 'dh.ih.s')

def test_hierarchical(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        q = c.query_graph(c.word).order_by(c.word.begin)

        results = q.all()
        id = results[1].id

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == 'this')
        assert([x.label for x in model.phone] == ['dh','ih','s'])

        q = c.query_graph(c.phone).order_by(c.phone.begin)

        results = q.all()
        id = results[1].id

        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.label == 'dh')
        assert(model.word.label == 'this')

def test_subannotations(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).columns(c.phone.voicing_during_closure.id.column_name('voicing_ids'))
        res = q.all()

        id = res[0].voicing_ids[0]
        model = SubAnnotation(c)
        model.load(id)
        assert(model._type == 'voicing_during_closure')
        assert(round(model.duration, 2) == 0.03)

def test_add_subannotation(subannotation_config):
    with CorpusContext(subannotation_config) as c:
        q = c.query_graph(c.phone).order_by(c.phone.id)
        res = q.all()
        id = res[0].id
        model = LinguisticAnnotation(c)
        model.load(id)
        assert(model.voicing_during_closure == [])

        model.add_subannotation('voicing_during_closure', 100, 101)
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
        id = res[0].id
        model = LinguisticAnnotation(c)
        model.load(id)

        assert(model.voicing_during_closure[0].begin == 99)
