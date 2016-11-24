
import pytest
import os

from polyglotdb.io import inspect_csv

from polyglotdb.io.types.content import (OrthographyAnnotationType,
                                        TranscriptionAnnotationType,
                                        NumericAnnotationType)

from polyglotdb.io.helper import guess_type

from polyglotdb.exceptions import DelimiterError
from polyglotdb import CorpusContext

def test_to_csv(graph_db, export_test_dir):
    export_path = os.path.join(export_test_dir, 'results_export.csv')
    with CorpusContext('acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.label.column_name('label'),
                    g.phone.duration.column_name('duration'),
                    g.phone.begin.column_name('begin'))
        q = q.order_by(g.phone.begin.column_name('begin'))
        q.to_csv(export_path)

    #ignore ids
    expected = [['label','duration','begin'],
                ['aa','0.0783100000000001','2.70424'],
                ['aa','0.12199999999999989','9.32077'],
                ['aa','0.03981000000000279','24.56029']]
    with open(export_path, 'r') as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            if line == '':
                continue
            line = line.split(',')
            print(line)
            assert(line == expected[i])
            i += 1

    with CorpusContext('acoustic', **graph_db) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.label,
                    g.phone.duration,
                    g.phone.begin)
        q = q.order_by(g.phone.begin)
        q.to_csv(export_path)

    #ignore ids
    expected = [['node_phone_label','node_phone_duration','node_phone_begin'],
                ['aa','0.0783100000000001','2.70424'],
                ['aa','0.12199999999999989','9.32077'],
                ['aa','0.03981000000000279','24.56029']]
    with open(export_path, 'r') as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            if line == '':
                continue
            line = line.split(',')
            print(line)
            assert(line == expected[i])
            i += 1


def test_inspect_example(csv_test_dir):
    example_path = os.path.join(csv_test_dir, 'example.txt')
    parser = inspect_csv(example_path)
    assert(parser.column_delimiter == ',')
    for a in parser.annotation_types:
        if a.name == 'frequency':
            assert(isinstance(a, NumericAnnotationType))
        elif a.name == 'transcription':
            assert(isinstance(a, TranscriptionAnnotationType))
            assert(a.trans_delimiter == '.')
        elif a.name == 'spelling':
            assert(isinstance(a, OrthographyAnnotationType))


@pytest.mark.xfail
def test_corpus_csv(graph_db, csv_test_dir):
    example_path = os.path.join(csv_test_dir, 'example.txt')

    with CorpusContext('basic_csv', **graph_db) as c:
        c.reset()
        parser = inspect_csv(example_path)
        parser.column_delimiter = '\t'
        with pytest.raises(DelimiterError):
            c.load(parser, example_path)

    with CorpusContext('basic_csv', **graph_db) as c:
        parser = inspect_csv(example_path)
        parser.annotation_types[1].name = 'word'
        c.load(parser, example_path)

        assert(c.lexicon['mata'].frequency == 2)
        assert(c.lexicon['mata'].transcription == 'm.ɑ.t.ɑ')


@pytest.mark.xfail
def test_corpus_csv_tiered(graph_db, csv_test_dir):
    example_path = os.path.join(csv_test_dir, 'tiered.txt')

    with CorpusContext('tiered_csv', **graph_db) as c:
        c.reset()
        parser = inspect_csv(example_path)

        parser.annotation_types[0].name = 'word'
        c.load(parser, example_path)

        assert(c.lexicon['tusi'].frequency == 13)
        assert(c.lexicon['tusi'].transcription == 't.u.s.i')
        #assert(c.lexicon['tusi'].vowel_tier == 'u.i')

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
def test_stressed(graph_db, csv_test_dir):
    stressed_path = os.path.join(csv_test_dir, 'stressed.txt')

    with CorpusContext('stressed_csv', **graph_db) as c:
        c.reset()
        parser = inspect_csv(stressed_path)
        parser.annotation_types[0].name = 'word'
        parser.annotation_types[1].number_behavior = 'stress'
        c.load(parser, stressed_path)

