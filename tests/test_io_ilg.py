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

def test_inspect_ilg_directory(ilg_test_dir):
    annotypes = inspect_discourse_ilg(ilg_test_dir)
    assert(len(annotypes) == 2)


def test_export_ilg(graph_db, export_test_dir):
    export_path = os.path.join(export_test_dir, 'export_ilg.txt')
    with CorpusContext(corpus_name = 'untimed', **graph_db) as c:
        export_discourse_ilg(c, 'test', export_path,
                annotations = ['label','transcription'], words_per_line = 3)
    expected_lines = ['cats are cute',
                        'k.ae.t.s aa.r k.uw.t',
                        'dogs are too',
                        'd.aa.g.z aa.r t.uw',
                        'i guess',
                        'ay g.eh.s']
    with open(export_path, 'r') as f:
        for i, line in enumerate(f):
            assert(line.strip() == expected_lines[i])

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
