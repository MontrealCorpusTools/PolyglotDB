import pytest
import os

from polyglotdb.io.helper import BaseAnnotation, Annotation, AnnotationType, DiscourseData

from polyglotdb.io.textgrid import inspect_discourse_textgrid, load_discourse_textgrid

from polyglotdb.corpus import CorpusContext
from polyglotdb.config import CorpusConfig


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
def globalphone_test_dir(test_dir):
    return os.path.join(test_dir, 'globalphone')

@pytest.fixture(scope='session')
def timit_test_dir(test_dir):
    return os.path.join(test_dir, 'timit')

@pytest.fixture(scope='session')
def textgrid_test_dir(test_dir):
    return os.path.join(test_dir, 'textgrids')

@pytest.fixture(scope='session')
def text_transcription_test_dir(test_dir):
    return os.path.join(test_dir, 'text_transcription')

@pytest.fixture(scope='session')
def text_spelling_test_dir(test_dir):
    return os.path.join(test_dir, 'text_spelling')

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

    annotations['phone'][0].super_id = annotations['word'][0].id
    annotations['phone'][1].super_id = annotations['word'][0].id
    annotations['phone'][2].super_id = annotations['word'][0].id
    annotations['phone'][3].super_id = annotations['word'][0].id
    annotations['phone'][4].super_id = annotations['word'][1].id
    annotations['phone'][5].super_id = annotations['word'][1].id
    annotations['phone'][6].super_id = annotations['word'][2].id
    annotations['phone'][7].super_id = annotations['word'][2].id
    annotations['phone'][8].super_id = annotations['word'][2].id
    annotations['phone'][9].super_id = annotations['word'][3].id
    annotations['phone'][10].super_id = annotations['word'][3].id
    annotations['phone'][11].super_id = annotations['word'][3].id
    annotations['phone'][12].super_id = annotations['word'][3].id
    annotations['phone'][13].super_id = annotations['word'][4].id
    annotations['phone'][14].super_id = annotations['word'][4].id
    annotations['phone'][15].super_id = annotations['word'][5].id
    annotations['phone'][16].super_id = annotations['word'][5].id
    annotations['phone'][17].super_id = annotations['word'][6].id
    annotations['phone'][18].super_id = annotations['word'][7].id
    annotations['phone'][19].super_id = annotations['word'][7].id
    annotations['phone'][20].super_id = annotations['word'][7].id

    annotations['word'][0].super_id = annotations['line'][0].id
    annotations['word'][1].super_id = annotations['line'][0].id
    annotations['word'][2].super_id = annotations['line'][0].id
    annotations['word'][3].super_id = annotations['line'][1].id
    annotations['word'][4].super_id = annotations['line'][1].id
    annotations['word'][5].super_id = annotations['line'][1].id
    annotations['word'][6].super_id = annotations['line'][2].id
    annotations['word'][7].super_id = annotations['line'][2].id
    data.add_annotations(**annotations)
    return data

@pytest.fixture(scope='session')
def corpus_data_untimed():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('transcription', None, None, token = False),
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
                            Annotation('dog', phone =  (9,12)),
                            Annotation('PL', phone =  (12,13)),
                            Annotation('are', phone =  (13,15)),
                            Annotation('too', phone =  (15,17)),
                            Annotation('i', phone =  (17,18)),
                            Annotation('guess', phone = (18,21)),
                            ],
                    'word':[
                            Annotation('cats', phone = (0,4), type_properties = {'transcription': 'k.ae.t.s'}),
                            Annotation('are', phone = (4,6), type_properties = {'transcription': 'aa.r'}),
                            Annotation('cute', phone = (6,9), type_properties = {'transcription': 'k.uw.t'}),
                            Annotation('dogs', phone =  (9,13), type_properties = {'transcription': 'd.aa.g.z'}),
                            Annotation('are', phone =  (13,15), type_properties = {'transcription': 'aa.r'}),
                            Annotation('too', phone =  (15,17), type_properties = {'transcription': 't.uw'}),
                            Annotation('i', phone =  (17,18), type_properties = {'transcription': 'ay'}),
                            Annotation('guess', phone = (18,21), type_properties = {'transcription': 'g.eh.s'}),
                            ],
                    'line': [
                            Annotation('', phone = (0,9)),
                            Annotation('', phone = (9,17)),
                            Annotation('', phone =  (17,21))
                            ]
                    }

    annotations['phone'][0].super_id = annotations['word'][0].id
    annotations['phone'][1].super_id = annotations['word'][0].id
    annotations['phone'][2].super_id = annotations['word'][0].id
    annotations['phone'][3].super_id = annotations['word'][0].id
    annotations['phone'][4].super_id = annotations['word'][1].id
    annotations['phone'][5].super_id = annotations['word'][1].id
    annotations['phone'][6].super_id = annotations['word'][2].id
    annotations['phone'][7].super_id = annotations['word'][2].id
    annotations['phone'][8].super_id = annotations['word'][2].id
    annotations['phone'][9].super_id = annotations['word'][3].id
    annotations['phone'][10].super_id = annotations['word'][3].id
    annotations['phone'][11].super_id = annotations['word'][3].id
    annotations['phone'][12].super_id = annotations['word'][3].id
    annotations['phone'][13].super_id = annotations['word'][4].id
    annotations['phone'][14].super_id = annotations['word'][4].id
    annotations['phone'][15].super_id = annotations['word'][5].id
    annotations['phone'][16].super_id = annotations['word'][5].id
    annotations['phone'][17].super_id = annotations['word'][6].id
    annotations['phone'][18].super_id = annotations['word'][7].id
    annotations['phone'][19].super_id = annotations['word'][7].id
    annotations['phone'][20].super_id = annotations['word'][7].id

    annotations['morpheme'][0].super_id = annotations['word'][0].id
    annotations['morpheme'][1].super_id = annotations['word'][0].id
    annotations['morpheme'][2].super_id = annotations['word'][1].id
    annotations['morpheme'][3].super_id = annotations['word'][2].id
    annotations['morpheme'][4].super_id = annotations['word'][3].id
    annotations['morpheme'][5].super_id = annotations['word'][3].id
    annotations['morpheme'][6].super_id = annotations['word'][4].id
    annotations['morpheme'][7].super_id = annotations['word'][5].id
    annotations['morpheme'][8].super_id = annotations['word'][6].id
    annotations['morpheme'][9].super_id = annotations['word'][7].id

    annotations['word'][0].super_id = annotations['line'][0].id
    annotations['word'][1].super_id = annotations['line'][0].id
    annotations['word'][2].super_id = annotations['line'][0].id
    annotations['word'][3].super_id = annotations['line'][1].id
    annotations['word'][4].super_id = annotations['line'][1].id
    annotations['word'][5].super_id = annotations['line'][1].id
    annotations['word'][6].super_id = annotations['line'][2].id
    annotations['word'][7].super_id = annotations['line'][2].id

    data.add_annotations(**annotations)
    return data


@pytest.fixture(scope='session')
def corpus_data_ur_sr():
    levels = [AnnotationType('sr', None, 'word', base = True, token = True),
                AnnotationType('word','sr','line', anchor = True),
                AnnotationType('ur', None, None, token = False),
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
                            Annotation('cats', type_properties = {'ur':['k','ae','t','s']}, sr =  (0,3)),
                            Annotation('are', type_properties = {'ur':['aa','r']}, sr =  (3,5)),
                            Annotation('cute', type_properties = {'ur':['k','uw','t']}, sr =  (5,7)),
                            Annotation('dogs', type_properties = {'ur':['d','aa','g','z']}, sr =  (7,12)),
                            Annotation('are', type_properties = {'ur':['aa','r']}, sr =  (12,14)),
                            Annotation('too', type_properties = {'ur':['t','uw']}, sr =  (14,16)),
                            Annotation('i', type_properties = {'ur':['ay']}, sr =  (16,17)),
                            Annotation('guess', type_properties = {'ur':['g','eh','s']}, sr =  (17,20)),
                            ],
                    'line': [
                            Annotation('', sr = (0,7)),
                            Annotation('', sr = (7,16)),
                            Annotation('', sr =  (16,20))
                            ]
                    }

    annotations['sr'][0].super_id = annotations['word'][0].id
    annotations['sr'][1].super_id = annotations['word'][0].id
    annotations['sr'][2].super_id = annotations['word'][0].id
    annotations['sr'][3].super_id = annotations['word'][1].id
    annotations['sr'][4].super_id = annotations['word'][1].id
    annotations['sr'][5].super_id = annotations['word'][2].id
    annotations['sr'][6].super_id = annotations['word'][2].id
    annotations['sr'][7].super_id = annotations['word'][3].id
    annotations['sr'][8].super_id = annotations['word'][3].id
    annotations['sr'][9].super_id = annotations['word'][3].id
    annotations['sr'][10].super_id = annotations['word'][3].id
    annotations['sr'][11].super_id = annotations['word'][3].id
    annotations['sr'][12].super_id = annotations['word'][4].id
    annotations['sr'][13].super_id = annotations['word'][4].id
    annotations['sr'][14].super_id = annotations['word'][5].id
    annotations['sr'][15].super_id = annotations['word'][5].id
    annotations['sr'][16].super_id = annotations['word'][6].id
    annotations['sr'][17].super_id = annotations['word'][7].id
    annotations['sr'][18].super_id = annotations['word'][7].id
    annotations['sr'][19].super_id = annotations['word'][7].id

    annotations['word'][0].super_id = annotations['line'][0].id
    annotations['word'][1].super_id = annotations['line'][0].id
    annotations['word'][2].super_id = annotations['line'][0].id
    annotations['word'][3].super_id = annotations['line'][1].id
    annotations['word'][4].super_id = annotations['line'][1].id
    annotations['word'][5].super_id = annotations['line'][1].id
    annotations['word'][6].super_id = annotations['line'][2].id
    annotations['word'][7].super_id = annotations['line'][2].id
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
                AnnotationType('word','phone',None, anchor = True)]
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
    annotations['phone'][0].super_id = annotations['word'][0].id
    annotations['phone'][1].super_id = annotations['word'][0].id
    annotations['phone'][2].super_id = annotations['word'][0].id
    annotations['phone'][3].super_id = annotations['word'][0].id
    annotations['phone'][4].super_id = annotations['word'][0].id
    annotations['phone'][5].super_id = annotations['word'][0].id
    annotations['phone'][6].super_id = annotations['word'][1].id
    annotations['phone'][7].super_id = annotations['word'][1].id
    annotations['phone'][8].super_id = annotations['word'][2].id
    annotations['phone'][9].super_id = annotations['word'][2].id
    annotations['phone'][10].super_id = annotations['word'][2].id
    annotations['phone'][11].super_id = annotations['word'][3].id
    annotations['phone'][12].super_id = annotations['word'][3].id
    annotations['phone'][13].super_id = annotations['word'][3].id
    annotations['phone'][14].super_id = annotations['word'][3].id
    annotations['phone'][15].super_id = annotations['word'][3].id

    annotations['syllable'][0].super_id = annotations['word'][0].id
    annotations['syllable'][1].super_id = annotations['word'][0].id
    annotations['syllable'][2].super_id = annotations['word'][1].id
    annotations['syllable'][3].super_id = annotations['word'][2].id
    annotations['syllable'][4].super_id = annotations['word'][3].id
    annotations['syllable'][5].super_id = annotations['word'][3].id

    annotations['morpheme'][0].super_id = annotations['word'][0].id
    annotations['morpheme'][1].super_id = annotations['word'][0].id
    annotations['morpheme'][2].super_id = annotations['word'][1].id
    annotations['morpheme'][3].super_id = annotations['word'][2].id
    annotations['morpheme'][4].super_id = annotations['word'][3].id
    annotations['morpheme'][5].super_id = annotations['word'][3].id

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
    return 'test'

@pytest.fixture(scope='session')
def graph_host():
    return 'localhost'

@pytest.fixture(scope='session')
def graph_port():
    return 7474

@pytest.fixture(scope='session')
def graph_db(graph_host, graph_port, graph_user, graph_pw):
    return dict(graph_host = graph_host, graph_port = graph_port)


@pytest.fixture(scope='session')
def untimed_config(graph_db,corpus_data_untimed):
    config = CorpusConfig('untimed', **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types({corpus_data_untimed.name: corpus_data_untimed})
        c.initialize_import(corpus_data_untimed)
        c.add_discourse(corpus_data_untimed)
        c.finalize_import(corpus_data_untimed)
    return config

@pytest.fixture(scope='session')
def timed_config(graph_db, corpus_data_timed):
    config = CorpusConfig('timed', **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types({corpus_data_timed.name: corpus_data_timed})
        c.initialize_import(corpus_data_timed)
        c.add_discourse(corpus_data_timed)
        c.finalize_import(corpus_data_timed)
    return config

@pytest.fixture(scope='session')
def syllable_morpheme_config(graph_db, corpus_data_syllable_morpheme):
    config = CorpusConfig('syllable_morpheme', **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types({corpus_data_syllable_morpheme.name: corpus_data_syllable_morpheme})
        c.initialize_import(corpus_data_syllable_morpheme)
        c.add_discourse(corpus_data_syllable_morpheme)
        c.finalize_import(corpus_data_syllable_morpheme)
    return config


    #with CorpusContext(graph_user, graph_pw, 'syllable_morpheme_srur', graph_host, graph_port) as c:
    #    c.add_discourse(corpus_data_syllable_morpheme_srur)

@pytest.fixture(scope='session')
def ursr_config(graph_db, corpus_data_ur_sr):
    config = CorpusConfig('ur_sr', **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types({corpus_data_ur_sr.name: corpus_data_ur_sr})
        c.initialize_import(corpus_data_ur_sr)
        c.add_discourse(corpus_data_ur_sr)
        c.finalize_import(corpus_data_ur_sr)
    return config

@pytest.fixture(scope='session')
def acoustic_config(graph_db, textgrid_test_dir):
    config = CorpusConfig('acoustic', **graph_db)

    acoustic_path = os.path.join(textgrid_test_dir, 'acoustic_corpus.TextGrid')
    with CorpusContext(config) as c:
        c.reset()
        annotation_types = inspect_discourse_textgrid(acoustic_path)
        load_discourse_textgrid(c, acoustic_path, annotation_types)
        c.analyze_acoustics()
    return config
