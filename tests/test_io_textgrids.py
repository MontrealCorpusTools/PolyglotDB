
import pytest
import os


from polyglotdb.io.helper import AnnotationType, Annotation, BaseAnnotation

from polyglotdb.io.textgrid import (textgrid_to_data,
                    inspect_discourse_textgrid,
                    load_discourse_textgrid,
                    load_directory_textgrid)

from polyglotdb.corpus import CorpusContext

from polyglotdb.exceptions import TextGridError

#def test_guess_tiers(textgrid_test_dir):
#    tg = load_textgrid(os.path.join(textgrid_test_dir,'phone_word.TextGrid'))
#    result = guess_tiers(tg)
#    assert(result[0] == ['word'])
#    assert(result[1] == ['phone'])
#    assert(result[2] == [])



def test_basic(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir,'phone_word.TextGrid')
    data = textgrid_to_data(path, [AnnotationType('word','phone',None, anchor=True),
                                AnnotationType('phone',None,None, base=True)])
    expected_words = []

    a = Annotation('sil')
    a.references.append('phone')
    a.begins.append(0)
    a.ends.append(1)
    expected_words.append(a)

    a = Annotation('a')
    a.references.append('phone')
    a.begins.append(1)
    a.ends.append(3)
    expected_words.append(a)

    a = Annotation('sil')
    a.references.append('phone')
    a.begins.append(3)
    a.ends.append(4)
    expected_words.append(a)
    assert(data['word']._list == expected_words)

    assert(data['phone']._list == [BaseAnnotation('?', 0, 0.25),
                        BaseAnnotation('a', 0.25, 0.5),
                        BaseAnnotation('b', 0.5, 0.75),
                        BaseAnnotation('?', 0.75, 1)])

def test_load(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid', **graph_db) as c:
        annotation_types = inspect_discourse_textgrid(path)
        print(annotation_types)
        load_discourse_textgrid(c, path, annotation_types)

def test_directory(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, 'phone_word.TextGrid')
    with CorpusContext('test_textgrid_directory', **graph_db) as c:
        with pytest.raises(TextGridError):
            annotation_types = inspect_discourse_textgrid(path)
            load_directory_textgrid(c, textgrid_test_dir, annotation_types)

def test_inspect_textgrid_directory(textgrid_test_dir):
    annotation_types = inspect_discourse_textgrid(textgrid_test_dir)
    assert(len(annotation_types) == 4)

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
        annotation_types = inspect_discourse_textgrid(path)
        load_discourse_textgrid(c, path, annotation_types)
