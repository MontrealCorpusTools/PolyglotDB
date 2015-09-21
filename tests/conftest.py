import pytest
import os

from annograph.io.helper import BaseAnnotation, Annotation, AnnotationType, DiscourseData

from annograph.io.textgrid import inspect_discourse_textgrid, load_discourse_textgrid

from annograph.corpus import CorpusContext


@pytest.fixture(scope='session')
def show_plots():
    return False
    if os.environ.get('TRAVIS'):
        return False
    return True

@pytest.fixture(scope='session')
def test_dir():
    if not os.path.exists('tests/data/generated'):
        os.makedirs('tests/data/generated')
    return os.path.abspath('tests/data')

@pytest.fixture(scope='session')
def buckeye_test_dir(test_dir):
    return os.path.join(test_dir, 'buckeye')

@pytest.fixture(scope='session')
def timit_test_dir(test_dir):
    return os.path.join(test_dir, 'timit')

@pytest.fixture(scope='session')
def textgrid_test_dir(test_dir):
    return os.path.join(test_dir, 'textgrids')

@pytest.fixture(scope='session')
def text_test_dir(test_dir):
    return os.path.join(test_dir, 'text')

@pytest.fixture(scope='session')
def ilg_test_dir(test_dir):
    return os.path.join(test_dir, 'ilg')

@pytest.fixture(scope='session')
def csv_test_dir(test_dir):
    return os.path.join(test_dir, 'csv')

@pytest.fixture(scope='session')
def features_test_dir(test_dir):
    return os.path.join(test_dir, 'features')

@pytest.fixture(scope='session')
def export_test_dir(test_dir):
    path = os.path.join(test_dir, 'export')
    if not os.path.exists(path):
        os.makedirs(path)
    return path

@pytest.fixture(scope='session')
def corpus_data_timed():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {
                    'phone':[BaseAnnotation('k', 0.0, 0.1),
                            BaseAnnotation('ae', 0.1, 0.2),
                            BaseAnnotation('t', 0.2, 0.3),
                            BaseAnnotation('s', 0.3, 0.4),
                            BaseAnnotation('aa', 0.5, 0.6),
                            BaseAnnotation('r',  0.6, 0.7),
                            BaseAnnotation('k', 0.8, 0.9),
                            BaseAnnotation('u', 0.9, 1.0),
                            BaseAnnotation('t', 1.0, 1.1),
                            BaseAnnotation('d', 2.0,  2.1),
                            BaseAnnotation('aa', 2.1, 2.2),
                            BaseAnnotation('g', 2.2, 2.3),
                            BaseAnnotation('z', 2.3, 2.4),
                            BaseAnnotation('aa', 2.4, 2.5),
                            BaseAnnotation('r', 2.5, 2.6),
                            BaseAnnotation('t', 2.6, 2.7),
                            BaseAnnotation('uw', 2.7, 2.8),
                            BaseAnnotation('ay', 3.0, 3.1),
                            BaseAnnotation('g', 3.3, 3.4),
                            BaseAnnotation('eh', 3.4, 3.5),
                            BaseAnnotation('s', 3.5, 3.6),
                            ],
                    'word':[
                            Annotation('cats', phone = (0,4)),
                            Annotation('are', phone = (4,6)),
                            Annotation('cute', phone = (6,9)),
                            Annotation('dogs', phone =  (9,13)),
                            Annotation('are', phone =  (13,15)),
                            Annotation('too', phone =  (15,17)),
                            Annotation('i', phone =  (17,18)),
                            Annotation('guess', phone = (18,21)),
                            ],
                    'line': [
                            Annotation('', phone = (0,9)),
                            Annotation('', phone = (9,17)),
                            Annotation('', phone =  (17,21))
                            ]
                    }
    data.add_annotations(**annotations)
    return data

@pytest.fixture(scope='session')
def corpus_data_untimed():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('morpheme', 'phone', 'word'),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {'phone':[BaseAnnotation('k'),
                            BaseAnnotation('ae'),
                            BaseAnnotation('t'),
                            BaseAnnotation('s'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('r'),
                            BaseAnnotation('k'),
                            BaseAnnotation('u'),
                            BaseAnnotation('t'),
                            BaseAnnotation('d'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('g'),
                            BaseAnnotation('z'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('r'),
                            BaseAnnotation('t'),
                            BaseAnnotation('uw'),
                            BaseAnnotation('ay'),
                            BaseAnnotation('g'),
                            BaseAnnotation('eh'),
                            BaseAnnotation('s'),
                            ],
                    'morpheme':[
                            Annotation('cat', phone = (0,3)),
                            Annotation('PL', phone = (3,4)),
                            Annotation('are', phone = (4,6)),
                            Annotation('cute', phone = (6,9)),
                            Annotation('dogs', phone =  (9,12)),
                            Annotation('PL', phone =  (12,13)),
                            Annotation('are', phone =  (13,15)),
                            Annotation('too', phone =  (15,17)),
                            Annotation('i', phone =  (17,18)),
                            Annotation('guess', phone = (18,21)),
                            ],
                    'word':[
                            Annotation('cats', phone = (0,4)),
                            Annotation('are', phone = (4,6)),
                            Annotation('cute', phone = (6,9)),
                            Annotation('dogs', phone =  (9,13)),
                            Annotation('are', phone =  (13,15)),
                            Annotation('too', phone =  (15,17)),
                            Annotation('i', phone =  (17,18)),
                            Annotation('guess', phone = (18,21)),
                            ],
                    'line': [
                            Annotation('', phone = (0,9)),
                            Annotation('', phone = (9,17)),
                            Annotation('', phone =  (17,21))
                            ]
                    }
    data.add_annotations(**annotations)
    return data


@pytest.fixture(scope='session')
def corpus_data_ur_sr():
    levels = [AnnotationType('sr', None, 'word', base = True, token = True),
                AnnotationType('word','sr','line', anchor = True),
                AnnotationType('line', 'word', None, anchor = False)]
    data = DiscourseData('test',levels)
    annotations = {'sr':[BaseAnnotation('k', 0.0, 0.1),
                            BaseAnnotation('ae', 0.1, 0.2),
                            BaseAnnotation('s', 0.2, 0.4),
                            BaseAnnotation('aa', 0.5, 0.6),
                            BaseAnnotation('r', 0.6, 0.7),
                            BaseAnnotation('k', 0.8, 0.9),
                            BaseAnnotation('u', 0.9, 1.1),
                            BaseAnnotation('d',  2.0, 2.1),
                            BaseAnnotation('aa', 2.1, 2.2),
                            BaseAnnotation('g', 2.2, 2.25),
                            BaseAnnotation('ah', 2.25, 2.3),
                            BaseAnnotation('z', 2.3, 2.4),
                            BaseAnnotation('aa', 2.4, 2.5),
                            BaseAnnotation('r', 2.5, 2.6),
                            BaseAnnotation('t', 2.6, 2.7),
                            BaseAnnotation('uw', 2.7, 2.8),
                            BaseAnnotation('ay', 3.0, 3.1),
                            BaseAnnotation('g', 3.3, 3.4),
                            BaseAnnotation('eh', 3.4, 3.5),
                            BaseAnnotation('s', 3.5, 3.6),
                            ],
                    'word':[
                            Annotation('cats', ur = ['k','ae','t','s'], sr =  (0,3)),
                            Annotation('are', ur = ['aa','r'], sr =  (3,5)),
                            Annotation('cute', ur = ['k','uw','t'], sr =  (5,7)),
                            Annotation('dogs', ur =  ['d','aa','g','z'], sr =  (7,12)),
                            Annotation('are', ur =  ['aa','r'], sr =  (12,14)),
                            Annotation('too', ur =  ['t','uw'], sr =  (14,16)),
                            Annotation('i', ur =  ['ay'], sr =  (16,17)),
                            Annotation('guess', ur = ['g','eh','s'], sr =  (17,20)),
                            ],
                    'line': [
                            Annotation('', sr = (0,7)),
                            Annotation('', sr = (7,16)),
                            Annotation('', sr =  (16,20))
                            ]
                    }
    data.add_annotations(**annotations)
    return data


@pytest.fixture(scope='session')
def lexicon_data():
    corpus_data = [{'spelling':'atema','transcription':['ɑ','t','e','m','ɑ'],'frequency':11.0},
                    {'spelling':'enuta','transcription':['e','n','u','t','ɑ'],'frequency':11.0},
                    {'spelling':'mashomisi','transcription':['m','ɑ','ʃ','o','m','i','s','i'],'frequency':5.0},
                    {'spelling':'mata','transcription':['m','ɑ','t','ɑ'],'frequency':2.0},
                    {'spelling':'nata','transcription':['n','ɑ','t','ɑ'],'frequency':2.0},
                    {'spelling':'sasi','transcription':['s','ɑ','s','i'],'frequency':139.0},
                    {'spelling':'shashi','transcription':['ʃ','ɑ','ʃ','i'],'frequency':43.0},
                    {'spelling':'shisata','transcription':['ʃ','i','s','ɑ','t','ɑ'],'frequency':3.0},
                    {'spelling':'shushoma','transcription':['ʃ','u','ʃ','o','m','ɑ'],'frequency':126.0},
                    {'spelling':'ta','transcription':['t','ɑ'],'frequency':67.0},
                    {'spelling':'tatomi','transcription':['t','ɑ','t','o','m','i'],'frequency':7.0},
                    {'spelling':'tishenishu','transcription':['t','i','ʃ','e','n','i','ʃ','u'],'frequency':96.0},
                    {'spelling':'toni','transcription':['t','o','n','i'],'frequency':33.0},
                    {'spelling':'tusa','transcription':['t','u','s','ɑ'],'frequency':32.0},
                    {'spelling':'ʃi','transcription':['ʃ','i'],'frequency':2.0}]
    return corpus_data


@pytest.fixture(scope='session')
def corpus_data_syllable_morpheme_srur():
    levels = [AnnotationType('ur', None, 'word', base = True, token = False),
                AnnotationType('sr', None, 'word', base = True, token = True),
                AnnotationType('syllable', 'sr', 'word'),
                AnnotationType('morpheme', 'ur', 'word'),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {'ur':[BaseAnnotation('b'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('k'),
                            BaseAnnotation('s'),
                            BaseAnnotation('ah'),
                            BaseAnnotation('z'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('r'),
                            BaseAnnotation('f'),
                            BaseAnnotation('ao'),
                            BaseAnnotation('r'),
                            BaseAnnotation('p'),
                            BaseAnnotation('ae'),
                            BaseAnnotation('k'),
                            BaseAnnotation('ih'),
                            BaseAnnotation('ng'),
                            ],
                    'sr':[BaseAnnotation('b'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('k'),
                            BaseAnnotation('s'),
                            BaseAnnotation('ah'),
                            BaseAnnotation('s'),
                            BaseAnnotation('er'),
                            BaseAnnotation('f'),
                            BaseAnnotation('er'),
                            BaseAnnotation('p'),
                            BaseAnnotation('ae'),
                            BaseAnnotation('k'),
                            BaseAnnotation('eng'),
                            ],
                    'syllable':[
                            Annotation('', sr = (0,3)),
                            Annotation('', sr = (3,6)),
                            Annotation('', sr = (6,7)),
                            Annotation('', sr = (7,9)),
                            Annotation('', sr =  (9,11)),
                            Annotation('', sr =  (11,13)),
                            ],
                    'morpheme':[
                            Annotation('box', ur = (0,4)),
                            Annotation('PL', ur = (4,6)),
                            Annotation('are', ur = (6,8)),
                            Annotation('for', ur = (8,11)),
                            Annotation('pack', ur =  (11,14)),
                            Annotation('PROG', ur =  (14,16)),
                            ],
                    'word':[
                            Annotation('boxes', ur = (0,6), sr = (0,6)),
                            Annotation('are', ur = (6,8), sr =  (6,7)),
                            Annotation('for', ur = (8,11), sr =  (7,9)),
                            Annotation('packing', ur =  (11,16), sr = (9,13)),
                            ],
                    'line':[Annotation('', sr = (0,13))]
                    }
    data.add_annotations(**annotations)
    return data

@pytest.fixture(scope='session')
def corpus_data_syllable_morpheme():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('syllable', 'phone', 'word'),
                AnnotationType('morpheme', 'phone', 'word'),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {'phone':[BaseAnnotation('b'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('k'),
                            BaseAnnotation('s'),
                            BaseAnnotation('ah'),
                            BaseAnnotation('z'),
                            BaseAnnotation('aa'),
                            BaseAnnotation('r'),
                            BaseAnnotation('f'),
                            BaseAnnotation('ao'),
                            BaseAnnotation('r'),
                            BaseAnnotation('p'),
                            BaseAnnotation('ae'),
                            BaseAnnotation('k'),
                            BaseAnnotation('ih'),
                            BaseAnnotation('ng'),
                            ],
                    'syllable':[
                            Annotation('', phone = (0,3)),
                            Annotation('', phone = (3,6)),
                            Annotation('', phone = (6,8)),
                            Annotation('', phone = (8,11)),
                            Annotation('', phone =  (11,13)),
                            Annotation('', phone =  (13,16)),
                            ],
                    'morpheme':[
                            Annotation('box', phone = (0,4)),
                            Annotation('PL', phone = (4,6)),
                            Annotation('are', phone = (6,8)),
                            Annotation('for', phone = (8,11)),
                            Annotation('pack', phone =  (11,14)),
                            Annotation('PROG', phone =  (14,16)),
                            ],
                    'word':[
                            Annotation('boxes', phone = (0,6)),
                            Annotation('are', phone = (6,8)),
                            Annotation('for', phone = (8,11)),
                            Annotation('packing', phone = (11,16)),
                            ]
                    }
    data.add_annotations(**annotations)
    return data




@pytest.fixture(scope='session')
def unspecified_test_corpus():
    return None
    corpus_data = [{'spelling':'atema','transcription':['ɑ','t','e','m','ɑ'],'frequency':11.0},
                    {'spelling':'enuta','transcription':['e','n','u','t','ɑ'],'frequency':11.0},
                    {'spelling':'mashomisi','transcription':['m','ɑ','ʃ','o','m','i','s','i'],'frequency':5.0},
                    {'spelling':'mata','transcription':['m','ɑ','t','ɑ'],'frequency':2.0},
                    {'spelling':'nata','transcription':['n','ɑ','t','ɑ'],'frequency':2.0},
                    {'spelling':'sasi','transcription':['s','ɑ','s','i'],'frequency':139.0},
                    {'spelling':'shashi','transcription':['ʃ','ɑ','ʃ','i'],'frequency':43.0},
                    {'spelling':'shisata','transcription':['ʃ','i','s','ɑ','t','ɑ'],'frequency':3.0},
                    {'spelling':'shushoma','transcription':['ʃ','u','ʃ','o','m','ɑ'],'frequency':126.0},
                    {'spelling':'ta','transcription':['t','ɑ'],'frequency':67.0},
                    {'spelling':'tatomi','transcription':['t','ɑ','t','o','m','i'],'frequency':7.0},
                    {'spelling':'tishenishu','transcription':['t','i','ʃ','e','n','i','ʃ','u'],'frequency':96.0},
                    {'spelling':'toni','transcription':['t','o','n','i'],'frequency':33.0},
                    {'spelling':'tusa','transcription':['t','u','s','ɑ'],'frequency':32.0},
                    {'spelling':'ʃi','transcription':['ʃ','i'],'frequency':2.0}]
    corpus = Corpus('test')
    for w in corpus_data:
        corpus.add_word(Word(**w))
    return corpus

@pytest.fixture(scope='session')
def graph_user():
    return 'neo4j'

@pytest.fixture(scope='session')
def graph_pw():
    return 'testtest'

@pytest.fixture(scope='session')
def graph_host():
    return 'localhost'

@pytest.fixture(scope='session')
def graph_port():
    return 7474


@pytest.fixture(scope='session')
def graph_db(graph_host, graph_port, graph_user, graph_pw,
            corpus_data_untimed, corpus_data_timed, corpus_data_syllable_morpheme,
            corpus_data_syllable_morpheme_srur, corpus_data_ur_sr,
            textgrid_test_dir):
    with CorpusContext(graph_user, graph_pw, 'untimed', graph_host, graph_port) as c:
        c.reset()
        c.add_discourse(corpus_data_untimed)

    with CorpusContext(graph_user, graph_pw, 'timed', graph_host, graph_port) as c:
        c.reset()
        c.add_discourse(corpus_data_timed)

    with CorpusContext(graph_user, graph_pw, 'syllable_morpheme', graph_host, graph_port) as c:
        c.reset()
        c.add_discourse(corpus_data_syllable_morpheme)

    #with CorpusContext(graph_user, graph_pw, 'syllable_morpheme_srur', graph_host, graph_port) as c:
    #    c.add_discourse(corpus_data_syllable_morpheme_srur)

    with CorpusContext(graph_user, graph_pw, 'ur_sr', graph_host, graph_port) as c:
        c.reset()
        c.add_discourse(corpus_data_ur_sr)

    acoustic_path = os.path.join(textgrid_test_dir, 'acoustic_corpus.TextGrid')
    with CorpusContext(graph_user, graph_pw, 'acoustic', graph_host, graph_port) as c:
        c.reset()
        annotation_types = inspect_discourse_textgrid(acoustic_path)
        load_discourse_textgrid(c, acoustic_path, annotation_types)
    return {'host':graph_host, 'port': graph_port, 'user': graph_user, 'password': graph_pw}
