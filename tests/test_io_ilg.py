import pytest
import os
import sys

from polyglotdb.io.text_ilg import (load_discourse_ilg,
                                            inspect_discourse_ilg,
                                            ilg_to_data, export_discourse_ilg)

from polyglotdb.io.helper import BaseAnnotation, Annotation, AnnotationType, Attribute

from polyglotdb.exceptions import DelimiterError, ILGWordMismatchError

from polyglotdb.corpus import CorpusContext

def test_inspect_ilg(ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, 'basic.txt')
    annotypes = inspect_discourse_ilg(basic_path)
    assert(len(annotypes) == 2)
    assert(annotypes[1].delimiter == '.')

@pytest.mark.xfail
def test_export_ilg(graph_db, export_test_dir, unspecified_test_corpus):
    d = generate_discourse(unspecified_test_corpus)
    export_path = os.path.join(export_test_dir, 'export_ilg.txt')
    export_discourse_ilg(d, export_path)

    d2 = load_discourse_ilg('test', export_path)

    for k in unspecified_test_corpus.keys():
        assert(d2.lexicon[k].spelling == unspecified_test_corpus[k].spelling)
        assert(d2.lexicon[k].transcription == unspecified_test_corpus[k].transcription)
        assert(d2.lexicon[k].frequency == unspecified_test_corpus[k].frequency)
    assert(d2.lexicon == unspecified_test_corpus)

def test_ilg_data(ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, 'basic.txt')
    tier_att = Attribute('transcription','tier')
    tier_att.delimiter = '.'
    ats = [AnnotationType('spelling', 'transcription',
                                        None, token = False, anchor = True),
                                    AnnotationType('transcription', None, None,
                                        token = False, base = True,
                                        attribute = tier_att)]
    ats[1].trans_delimiter = '.'
    data = ilg_to_data(basic_path, ats)

    expected_words = []
    a = Annotation('a')
    a.references.append('transcription')
    a.begins.append(0)
    a.ends.append(2)
    expected_words.append(a)

    a = Annotation('a')
    a.references.append('transcription')
    a.begins.append(2)
    a.ends.append(4)
    expected_words.append(a)

    a = Annotation('b')
    a.references.append('transcription')
    a.begins.append(4)
    a.ends.append(6)
    expected_words.append(a)

    assert(data['spelling']._list == expected_words)
    assert(data['transcription']._list == [BaseAnnotation('a'),
                                        BaseAnnotation('b'),
                                        BaseAnnotation('a'),
                                        BaseAnnotation('b'),
                                        BaseAnnotation('c'),
                                        BaseAnnotation('d')])

def test_ilg_basic(graph_db, ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, 'basic.txt')
    tier_att = Attribute('transcription','tier')
    tier_att.delimiter = '.'
    ats = [AnnotationType('spelling', 'transcription',
                                        None, token = False, anchor = True),
                                    AnnotationType('transcription', None, None,
                                        token = False, base = True,
                                        attribute = tier_att)]
    ats[1].trans_delimiter = '.'
    with CorpusContext(corpus_name = 'basic_ilg', **graph_db) as c:
        c.reset()
        load_discourse_ilg(c, basic_path, ats)
        assert(c.lexicon['a'].frequency == 2)

def test_ilg_mismatched(graph_db, ilg_test_dir):
    mismatched_path = os.path.join(ilg_test_dir, 'mismatched.txt')

    ats = [AnnotationType('spelling', 'transcription',
                                        None, token = False, anchor = True),
                                    AnnotationType('transcription', None, None,
                                        token = False, base = True,
                                        attribute = Attribute('transcription','tier'))]
    ats[1].trans_delimiter = '.'

    with CorpusContext(corpus_name = 'mismatch', **graph_db) as c:
        c.reset()
        with pytest.raises(ILGWordMismatchError):
            load_discourse_ilg(c, mismatched_path, ats)
