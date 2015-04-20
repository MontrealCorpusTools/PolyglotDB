import pytest
import os

from annograph.classes import Corpus

from annograph.helper import AnnotationType, DiscourseData

from annograph.io import add_discourse

@pytest.fixture(scope='session')
def show_plots():
    return False
    if os.environ.get('TRAVIS'):
        return False
    return True

@pytest.fixture(scope='module')
def test_dir():
    if not os.path.exists('tests/data/generated'):
        os.makedirs('tests/data/generated')
    return os.path.abspath('tests/data')

@pytest.fixture(scope='module')
def corpus_data_timed():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {
                    'phone':[{'label': 'k','begin': 0.0,'end': 0.1},
                            {'label': 'ae','begin': 0.1,'end': 0.2},
                            {'label': 't','begin': 0.2,'end': 0.3},
                            {'label': 's','begin': 0.3,'end': 0.4},
                            {'label': 'aa','begin': 0.5,'end': 0.6},
                            {'label': 'r', 'begin': 0.6,'end': 0.7},
                            {'label': 'k','begin': 0.8,'end': 0.9},
                            {'label': 'u','begin': 0.9,'end': 1.0},
                            {'label': 't','begin': 1.0,'end': 1.1},
                            {'label': 'd','begin': 2.0, 'end': 2.1},
                            {'label': 'aa','begin': 2.1,'end': 2.2},
                            {'label': 'g','begin': 2.2,'end': 2.3},
                            {'label': 'z','begin': 2.3,'end': 2.4},
                            {'label': 'aa','begin': 2.4,'end': 2.5},
                            {'label': 'r','begin': 2.5,'end': 2.6},
                            {'label': 't','begin': 2.6,'end': 2.7},
                            {'label': 'uw','begin': 2.7,'end': 2.8},
                            {'label': 'ay','begin': 3.0,'end': 3.1},
                            {'label': 'g','begin': 3.3,'end': 3.4},
                            {'label': 'eh','begin': 3.4,'end': 3.5},
                            {'label': 's','begin': 3.5,'end': 3.6},
                            ],
                    'word':[
                            {'label': 'cats','phone':(0,4)},
                            {'label': 'are','phone':(4,6)},
                            {'label': 'cute','phone':(6,9)},
                            {'label': 'dogs','phone': (9,13)},
                            {'label': 'are','phone': (13,15)},
                            {'label': 'too','phone': (15,17)},
                            {'label': 'i','phone': (17,18)},
                            {'label':'guess','phone':(18,21)},
                            ],
                    'line': [
                            {'label': '1','phone':(0,9)},
                            {'label': '2','phone':(9,13)},
                            {'label': '3','phone': (13,21)}
                            ]
                    }
    data.add_annotations(**annotations)
    return [data]

@pytest.fixture(scope='module')
def corpus_data_untimed():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('morpheme', 'phone', 'word'),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {'phone':[{'label': 'k'},
                            {'label': 'ae'},
                            {'label': 't'},
                            {'label': 's'},
                            {'label': 'aa'},
                            {'label': 'r'},
                            {'label': 'k'},
                            {'label': 'u'},
                            {'label': 't'},
                            {'label': 'd'},
                            {'label': 'aa'},
                            {'label': 'g'},
                            {'label': 'z'},
                            {'label': 'aa'},
                            {'label': 'r'},
                            {'label': 't'},
                            {'label': 'uw'},
                            {'label':'ay'},
                            {'label':'g'},
                            {'label':'eh'},
                            {'label':'s'},
                            ],
                    'morpheme':[
                            {'label': 'cat','phone':(0,3)},
                            {'label': 'PL','phone':(3,4)},
                            {'label': 'are','phone':(4,6)},
                            {'label': 'cute','phone':(6,9)},
                            {'label': 'dogs','phone': (9,12)},
                            {'label': 'PL','phone': (12,13)},
                            {'label': 'are','phone': (13,15)},
                            {'label': 'too','phone': (15,17)},
                            {'label': 'i','phone': (17,18)},
                            {'label':'guess','phone':(18,21)},
                            ],
                    'word':[
                            {'label': 'cats','phone':(0,4)},
                            {'label': 'are','phone':(4,6)},
                            {'label': 'cute','phone':(6,9)},
                            {'label': 'dogs','phone': (9,13)},
                            {'label': 'are','phone': (13,15)},
                            {'label': 'too','phone': (15,17)},
                            {'label': 'i','phone': (17,18)},
                            {'label':'guess','phone':(18,21)},
                            ],
                    'line': [
                            {'label': '1','phone':(0,9)},
                            {'label': '2','phone':(9,13)},
                            {'label': '3','phone': (13,21)}
                            ]
                    }
    data.add_annotations(**annotations)
    return [data]


@pytest.fixture(scope='module')
def corpus_data_ur_sr():
    levels = [AnnotationType('ur', None, 'word', base = True, token = False),
                AnnotationType('sr', None, 'word', base = True, token = True),
                AnnotationType('word','sr','line', anchor = True),
                AnnotationType('line', 'word', None, anchor = False)]
    data = DiscourseData('test',levels)
    annotations = {'ur':[{'label': 'k'},
                            {'label': 'ae'},
                            {'label': 't'},
                            {'label': 's'},
                            {'label': 'aa'},
                            {'label': 'r'},
                            {'label': 'k'},
                            {'label': 'u'},
                            {'label': 't'},
                            {'label': 'd'},
                            {'label': 'aa'},
                            {'label': 'g'},
                            {'label': 'z'},
                            {'label': 'aa'},
                            {'label': 'r'},
                            {'label': 't'},
                            {'label': 'uw'},
                            {'label': 'ay'},
                            {'label': 'g'},
                            {'label': 'eh'},
                            {'label': 's'},
                            ],
                    'sr':[{'label': 'k','begin': 0.0,'end': 0.1},
                            {'label': 'ae','begin': 0.1,'end': 0.2},
                            {'label': 's','begin': 0.2,'end': 0.4},
                            {'label': 'aa','begin': 0.5,'end': 0.6},
                            {'label': 'r','begin': 0.6,'end': 0.7},
                            {'label': 'k','begin': 0.8,'end': 0.9},
                            {'label': 'u','begin': 0.9,'end': 1.1},
                            {'label': 'd', 'begin': 2.0,'end': 2.1},
                            {'label': 'aa','begin': 2.1,'end': 2.2},
                            {'label': 'g','begin': 2.2,'end': 2.25},
                            {'label': 'ah','begin': 2.25,'end': 2.3},
                            {'label': 'z','begin': 2.3,'end': 2.4},
                            {'label': 'aa','begin': 2.4,'end': 2.5},
                            {'label': 'r','begin': 2.5,'end': 2.6},
                            {'label': 't','begin': 2.6,'end': 2.7},
                            {'label': 'uw','begin': 2.7,'end': 2.8},
                            {'label':'ay','begin': 3.0,'end': 3.1},
                            {'label':'g','begin': 3.3,'end': 3.4},
                            {'label':'eh','begin': 3.4,'end': 3.5},
                            {'label':'s','begin': 3.5, 'end': 3.6},
                            ],
                    'word':[
                            {'label': 'cats','ur':(0,4),'sr': (0,3)},
                            {'label': 'are','ur':(4,6),'sr': (3,5)},
                            {'label': 'cute','ur':(6,9),'sr': (5,7)},
                            {'label': 'dogs','ur': (9,13),'sr': (7,12)},
                            {'label': 'are','ur': (13,15),'sr': (12,14)},
                            {'label': 'too','ur': (15,17),'sr': (14,16)},
                            {'label': 'i','ur': (17,18),'sr': (16,17)},
                            {'label':'guess','ur':(18,21),'sr': (17,20)},
                            ],
                    'line': [
                            {'label': '1','sr':(0,7)},
                            {'label': '2','sr':(7,16)},
                            {'label': '3','sr': (16,20)}
                            ]
                    }
    data.add_annotations(**annotations)
    return [data]


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
def corpus_data_syllable_morpheme_srur():
    levels = [AnnotationType('ur', None, 'word', base = True, token = False),
                AnnotationType('sr', None, 'word', base = True, token = True),
                AnnotationType('syllable', 'sr', 'word'),
                AnnotationType('morpheme', 'ur', 'word'),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {'ur':[{'label': 'b'},
                            {'label': 'aa'},
                            {'label': 'k'},
                            {'label': 's'},
                            {'label': 'ah'},
                            {'label': 'z'},
                            {'label': 'aa'},
                            {'label': 'r'},
                            {'label': 'f'},
                            {'label': 'ao'},
                            {'label': 'r'},
                            {'label': 'p'},
                            {'label': 'ae'},
                            {'label': 'k'},
                            {'label': 'ih'},
                            {'label': 'ng'},
                            ],
                    'sr':[{'label': 'b'},
                            {'label': 'aa'},
                            {'label': 'k'},
                            {'label': 's'},
                            {'label': 'ah'},
                            {'label': 's'},
                            {'label': 'er'},
                            {'label': 'f'},
                            {'label': 'er'},
                            {'label': 'p'},
                            {'label': 'ae'},
                            {'label': 'k'},
                            {'label': 'eng'},
                            ],
                    'syllable':[
                            {'label': '(b.aa.k)','sr':(0,3)},
                            {'label': '(s.ah.s)','sr':(3,6)},
                            {'label': '(er)','sr':(6,7)},
                            {'label': '(f.er)','sr':(7,9)},
                            {'label': '(p.ae)','sr': (9,11)},
                            {'label': '(k.eng)','sr': (11,13)},
                            ],
                    'morpheme':[
                            {'label': 'box','ur':(0,4)},
                            {'label': 'PL','ur':(4,6)},
                            {'label': 'are','ur':(6,8)},
                            {'label': 'for','ur':(8,11)},
                            {'label': 'pack','ur': (11,14)},
                            {'label': 'PROG','ur': (14,16)},
                            ],
                    'word':[
                            {'label': 'boxes','ur':(0,6), 'sr':(0,6)},
                            {'label': 'are','ur':(6,8), 'sr': (6,7)},
                            {'label': 'for','ur':(8,11), 'sr': (7,9)},
                            {'label': 'packing','ur': (11,16), 'sr':(9,13)},
                            ],
                    'line':[{'label':'1', 'sr':(0,16)}]
                    }
    data.add_annotations(**annotations)
    return [data]

@pytest.fixture(scope='module')
def corpus_data_syllable_morpheme():
    levels = [AnnotationType('phone', None, 'word', base = True, token = True),
                AnnotationType('syllable', 'phone', 'word'),
                AnnotationType('morpheme', 'phone', 'word'),
                AnnotationType('word','phone','line', anchor = True),
                AnnotationType('line', 'word', None)]
    data = DiscourseData('test',levels)
    annotations = {'phone':[{'label': 'b'},
                            {'label': 'aa'},
                            {'label': 'k'},
                            {'label': 's'},
                            {'label': 'ah'},
                            {'label': 'z'},
                            {'label': 'aa'},
                            {'label': 'r'},
                            {'label': 'f'},
                            {'label': 'ao'},
                            {'label': 'r'},
                            {'label': 'p'},
                            {'label': 'ae'},
                            {'label': 'k'},
                            {'label': 'ih'},
                            {'label': 'ng'},
                            ],
                    'syllable':[
                            {'label': '(b.aa.k)','phone':(0,3)},
                            {'label': '(s.ah.z)','phone':(3,6)},
                            {'label': '(aa.r)','phone':(6,8)},
                            {'label': '(f.ao.r)','phone':(8,11)},
                            {'label': '(p.ae)','phone': (11,13)},
                            {'label': '(k.ih.ng)','phone': (13,16)},
                            ],
                    'morpheme':[
                            {'label': 'box','phone':(0,4)},
                            {'label': 'PL','phone':(4,6)},
                            {'label': 'are','phone':(6,8)},
                            {'label': 'for','phone':(8,11)},
                            {'label': 'pack','phone': (11,14)},
                            {'label': 'PROG','phone': (14,16)},
                            ],
                    'word':[
                            {'label': 'boxes','phone':(0,6)},
                            {'label': 'are','phone':(6,8)},
                            {'label': 'for','phone':(8,11)},
                            {'label': 'packing','phone': (11,16)},
                            ]
                    }
    data.add_annotations(**annotations)
    return [data]


@pytest.fixture(scope = 'module')
def timed_corpus(test_dir, corpus_data_timed):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_timed.db'))
    c.initial_setup()
    add_discourse(c,corpus_data_timed[0])
    return c

@pytest.fixture(scope = 'module')
def untimed_corpus(test_dir, corpus_data_untimed):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_untimed.db'))
    c.initial_setup()
    add_discourse(c, corpus_data_untimed[0])
    return c

@pytest.fixture(scope = 'module')
def syllable_morpheme_corpus(test_dir, corpus_data_syllable_morpheme):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_syllable_morpheme.db'))
    c.initial_setup()
    add_discourse(c, corpus_data_syllable_morpheme[0])
    return c

@pytest.fixture(scope = 'module')
def srur_corpus(test_dir, corpus_data_ur_sr):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_ur_sr.db'))
    c.initial_setup()
    add_discourse(c, corpus_data_ur_sr[0])
    return c
