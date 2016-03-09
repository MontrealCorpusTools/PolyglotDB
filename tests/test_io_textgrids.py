
import pytest
import os

from polyglotdb.io import inspect_textgrid

from polyglotdb.io.types.parsing import TobiTier, OrthographyTier

from polyglotdb.corpus import CorpusContext

from polyglotdb.exceptions import TextGridError, GraphQueryError

def test_tobi(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir, 'tobi.TextGrid')
    parser = inspect_textgrid(path)
    assert(isinstance(parser.annotation_types[0], TobiTier))
    assert(isinstance(parser.annotation_types[1], OrthographyTier))

@pytest.mark.xfail
def test_guess_tiers(textgrid_test_dir):
    tg = load_textgrid(os.path.join(textgrid_test_dir,'phone_word.TextGrid'))
    result = guess_tiers(tg)
    assert(result[0] == ['word'])
    assert(result[1] == ['phone'])
    assert(result[2] == [])

    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')

    tg = load_textgrid(path)
    spell, base, att = guess_tiers(tg)
    assert(len(spell) == 1)
    assert(len(base) == 0)
    assert(len(att) == 2)

def test_load(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid', **graph_db) as c:
        parser = inspect_textgrid(path)
        parser.annotation_types[1].linguistic_type = 'word'
        parser.annotation_types[2].ignored = True
        parser.hierarchy['word'] = None
        parser.hierarchy['phone'] = 'word'
        print([(x.linguistic_type, x.name) for x in parser.annotation_types])
        c.load(parser, path)

def test_directory(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid_directory', **graph_db) as c:
        with pytest.raises(TextGridError):
            parser = inspect_textgrid(path)
            c.load(parser, textgrid_test_dir)

@pytest.mark.xfail
def test_inspect_textgrid_directory(textgrid_test_dir):
    parser = inspect_textgrid(textgrid_test_dir)
    assert(len(parser.annotation_types) == 4)

@pytest.mark.xfail
def test_two_speakers(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir,'2speakers.TextGrid')
    data = textgrid_to_data(path, [AnnotationType('Speaker 1 - word','Speaker 1 - phone',None, anchor=True, speaker = 'Speaker 1'),
                                AnnotationType('Speaker 1 - phone',None,None, base=True, speaker = 'Speaker 1'),
                                AnnotationType('Speaker 2 - word','Speaker 2 - phone',None, anchor=True, speaker = 'Speaker 2'),
                                AnnotationType('Speaker 2 - phone',None,None, base=True, speaker = 'Speaker 2')])

def test_load_pronunciation_ignore(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')
    with CorpusContext('test_pronunc', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_types[1].ignored = True
        parser.annotation_types[2].ignored = True
        c.load(parser, path)


        with pytest.raises(GraphQueryError):
            q = c.query_graph(c.actualPron)
            results = q.all()

def test_load_pronunciation(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')

    with CorpusContext('test_pronunc', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_types[2].type_property = False
        c.load(parser, path)

        q = c.query_graph(c.words).filter(c.words.label == 'probably')
        q = q.order_by(c.words.begin)
        q = q.columns(c.words.label,
                c.words.dictionaryPron.column_name('dict_pron'),
                c.words.actualPron.column_name('act_pron'))
        results = q.all()
        assert(results[0].dict_pron == 'p.r.aa.b.ah.b.l.iy')
        assert(results[0].act_pron == 'p.r.aa.b.ah.b.l.iy')
