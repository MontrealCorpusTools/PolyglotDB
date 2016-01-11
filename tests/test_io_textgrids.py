
import pytest
import os

from polyglotdb.io import inspect_textgrid

from polyglotdb.io.types.parsing import TobiTier, OrthographyTier

from polyglotdb.corpus import CorpusContext

from polyglotdb.exceptions import TextGridError

def test_tobi(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir, 'tobi.TextGrid')
    parser = inspect_textgrid(path)
    assert(isinstance(parser.annotation_types[0], TobiTier))
    assert(isinstance(parser.annotation_types[1], OrthographyTier))

#def test_guess_tiers(textgrid_test_dir):
#    tg = load_textgrid(os.path.join(textgrid_test_dir,'phone_word.TextGrid'))
#    result = guess_tiers(tg)
#    assert(result[0] == ['word'])
#    assert(result[1] == ['phone'])
#    assert(result[2] == [])

def test_load(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid', **graph_db) as c:
        parser = inspect_textgrid(path)
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

def test_load_pronunciation(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'pronunc_variants_corpus.TextGrid')
    with CorpusContext('test_pronunc', **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        c.load(parser, path)
