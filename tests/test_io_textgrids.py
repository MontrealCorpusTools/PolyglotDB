import pytest
import os

from polyglotdb.io import inspect_textgrid

from polyglotdb.io.types.parsing import TobiTier, OrthographyTier

from polyglotdb import CorpusContext

from polyglotdb.exceptions import TextGridError, GraphQueryError


def test_tobi(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir, 'tobi.TextGrid')
    parser = inspect_textgrid(path)
    assert (isinstance(parser.annotation_tiers[0], TobiTier))
    assert (isinstance(parser.annotation_tiers[1], OrthographyTier))


@pytest.mark.xfail
def test_guess_tiers(textgrid_test_dir):
    tg = load_textgrid(os.path.join(textgrid_test_dir, 'phone_word.TextGrid'))
    result = guess_tiers(tg)
    assert (result[0] == ['word'])
    assert (result[1] == ['phone'])
    assert (result[2] == [])

    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')

    tg = load_textgrid(path)
    spell, base, att = guess_tiers(tg)
    assert (len(spell) == 1)
    assert (len(base) == 0)
    assert (len(att) == 2)


def test_load(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_tiers[1].linguistic_type = 'word'
        parser.annotation_tiers[2].ignored = True
        parser.hierarchy['word'] = None
        parser.hierarchy['phone'] = 'word'
        print([(x.linguistic_type, x.name) for x in parser.annotation_tiers])
        c.load(parser, path)


@pytest.mark.xfail
def test_directory(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid_directory', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        unparsed = c.load(parser, textgrid_test_dir)
        assert (len(unparsed) > 0)


@pytest.mark.xfail
def test_inspect_textgrid_directory(textgrid_test_dir):
    parser = inspect_textgrid(textgrid_test_dir)
    assert (len(parser.annotation_tiers) == 4)


@pytest.mark.xfail
def test_two_speakers(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir, '2speakers.TextGrid')
    data = textgrid_to_data(path, [
        AnnotationType('Speaker 1 - word', 'Speaker 1 - phone', None, anchor=True, speaker='Speaker 1'),
        AnnotationType('Speaker 1 - phone', None, None, base=True, speaker='Speaker 1'),
        AnnotationType('Speaker 2 - word', 'Speaker 2 - phone', None, anchor=True, speaker='Speaker 2'),
        AnnotationType('Speaker 2 - phone', None, None, base=True, speaker='Speaker 2')])


def test_load_pronunciation_ignore(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')
    with CorpusContext('test_pronunc', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_tiers[1].ignored = True
        parser.annotation_tiers[2].ignored = True
        c.load(parser, path)

        with pytest.raises(GraphQueryError):
            q = c.query_graph(c.actualPron)
            results = q.all()


def test_load_pronunciation(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')

    with CorpusContext('test_pronunc', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_tiers[2].type_property = False
        c.load(parser, path)

        q = c.query_graph(c.word).filter(c.word.label == 'probably')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label,
                      c.word.dictionaryPron.column_name('dict_pron'),
                      c.word.actualPron.column_name('act_pron'))
        results = q.all()
        assert (results[0]['dict_pron'] == 'p.r.aa.b.ah.b.l.iy')
        assert (results[0]['act_pron'] == 'p.r.aa.b.ah.b.l.iy')


def test_word_transcription(graph_db, textgrid_test_dir):
    with CorpusContext("discourse_textgrid", **graph_db) as c:
        c.reset()
        path = os.path.join(textgrid_test_dir, 'acoustic_corpus.TextGrid')
        parser = inspect_textgrid(path)
        c.load(parser, path)
        assert (c.hierarchy.has_type_property('word', 'transcription'))
