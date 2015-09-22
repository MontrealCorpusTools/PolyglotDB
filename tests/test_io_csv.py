
import pytest
import os

from annograph.io.csv import (load_corpus_csv, export_corpus_csv, inspect_csv,
                                        load_feature_matrix_csv, export_feature_matrix_csv)

from annograph.io.helper import BaseAnnotation, Annotation, AnnotationType, Attribute

from annograph.exceptions import DelimiterError
from annograph.corpus import CorpusContext

def test_inspect_example(csv_test_dir):
    example_path = os.path.join(csv_test_dir, 'example.txt')
    atts, coldelim = inspect_csv(example_path)
    assert(coldelim == ',')
    for a in atts:
        if a.name == 'frequency':
            assert(a.attribute.att_type == 'numeric')
        elif a.name == 'transcription':
            assert(a.attribute.att_type == 'tier')
            assert(a.delimiter == '.')
        elif a.name == 'spelling':
            assert(a.attribute.att_type == 'spelling')


def test_corpus_csv(graph_db, csv_test_dir, unspecified_test_corpus):
    example_path = os.path.join(csv_test_dir, 'example.txt')

    with CorpusContext(corpus_name = 'basic_csv', **graph_db) as c:
        c.reset()
        with pytest.raises(DelimiterError):
            load_corpus_csv(c, example_path,delimiter='\t')
    #with pytest.raises(DelimiterError):
    #    load_corpus_csv('example',example_path,delimiter=',')

    with CorpusContext(corpus_name = 'basic_csv', **graph_db) as c:
        load_corpus_csv(c,example_path,delimiter=',')

        assert(c.lexicon['mata'].frequency == 2)
        assert(c.lexicon['mata'].transcription == 'm.ɑ.t.ɑ')


@pytest.mark.xfail
def test_load_with_fm(self):
    c = load_transcription_corpus('test',self.transcription_path,' ',
                ['-','=','.'],trans_delimiter='.',
                feature_system_path = self.full_feature_matrix_path)

    self.assertEqual(c.lexicon.specifier,load_binary(self.full_feature_matrix_path))

    self.assertEqual(c.lexicon['cab'].frequency, 1)

    self.assertEqual(c.lexicon.check_coverage(),[])

    c = load_transcription_corpus('test',self.transcription_path,' ',
                ['-','=','.'],trans_delimiter='.',
                feature_system_path = self.missing_feature_matrix_path)

    self.assertEqual(c.lexicon.specifier,load_binary(self.missing_feature_matrix_path))

    self.assertEqual(sorted(c.lexicon.check_coverage()),sorted(['b','c','d']))


@pytest.mark.xfail
def test_basic_feature_matrix(features_test_dir):
    basic_path = os.path.join(features_test_dir, 'test_feature_matrix.txt')

    with pytest.raises(DelimiterError):
        load_feature_matrix_csv('test',basic_path,' ')

    fm = load_feature_matrix_csv('test',basic_path,',')

    assert(fm.name == 'test')
    assert(fm['a','feature1'] == '+')

@pytest.mark.xfail
def test_missing_value(features_test_dir):
    missing_value_path = os.path.join(features_test_dir, 'test_feature_matrix_missing_value.txt')
    fm = load_feature_matrix_csv('test',missing_value_path,',')

    assert(fm['d','feature2'] == 'n')

@pytest.mark.xfail
def test_extra_feature(features_test_dir):
    extra_feature_path = os.path.join(features_test_dir, 'test_feature_matrix_extra_feature.txt')
    fm = load_feature_matrix_csv('test',extra_feature_path,',')

    with pytest.raises(KeyError):
        fm.__getitem__(('a','feature3'))

@pytest.mark.xfail
def test_stressed(csv_test_dir):
    stressed_path = os.path.join(csv_test_dir, 'stressed.txt')
    ats,_ = inspect_csv(stressed_path, coldelim = ',')
    print(ats)
    ats[1].number_behavior = 'stress'
    c = load_corpus_csv('stressed',stressed_path,',', ats)
    assert(c.inventory['uw'].symbol == 'uw')
    assert(c.inventory.stresses == {'1': set(['uw','iy']),
                                    '0': set(['uw','iy','ah'])})
