import pytest

@pytest.fixture(scope='module')
def corpus_data_timed():
    discourses = [{'name': 'test',
                    'data': {
                    'phones':[{'label': 'k',
                                    'begin': 0.0,
                                    'end': 0.1},
                            {'label': 'ae',
                                    'begin': 0.1,
                                    'end': 0.2},
                            {'label': 't',
                                    'begin': 0.2,
                                    'end': 0.3},
                            {'label': 's',
                                    'begin': 0.3,
                                    'end': 0.4},
                            {'label': 'aa',
                                    'begin': 0.5,
                                    'end': 0.6},
                            {'label': 'r',
                                    'begin': 0.6,
                                    'end': 0.7},
                            {'label': 'k',
                                    'begin': 0.8,
                                    'end': 0.9},
                            {'label': 'u',
                                    'begin': 0.9,
                                    'end': 1.0},
                            {'label': 't',
                                    'begin': 1.0,
                                    'end': 1.1},
                            {'label': 'd',
                                    'begin': 2.0,
                                    'end': 2.1},
                            {'label': 'aa',
                                    'begin': 2.1,
                                    'end': 2.2},
                            {'label': 'g',
                                    'begin': 2.2,
                                    'end': 2.3},
                            {'label': 'z',
                                    'begin': 2.3,
                                    'end': 2.4},
                            {'label': 'aa',
                                    'begin': 2.4,
                                    'end': 2.5},
                            {'label': 'r',
                                    'begin': 2.5,
                                    'end': 2.6},
                            {'label': 't',
                                    'begin': 2.6,
                                    'end': 2.7},
                            {'label': 'uw',
                                    'begin': 2.7,
                                    'end': 2.8},
                            {'label':'ay',
                                    'begin': 3.0,
                                    'end': 3.1},
                            {'label':'g',
                                    'begin': 3.3,
                                    'end': 3.4},
                            {'label':'eh',
                                    'begin': 3.4,
                                    'end': 3.5},
                            {'label':'s',
                                    'begin': 3.5,
                                    'end': 3.6},
                            ],
                    'words':[
                            {'label': 'cats',
                            'phones':(0,4)
                            },
                            {'label': 'are',
                            'phones':(4,6)},
                            {'label': 'cute',
                            'phones':(6,9)},
                            {'label': 'dogs',
                            'phones': (9,13)
                                },
                            {'label': 'are',
                            'phones': (13,15)},
                            {'label': 'too',
                            'phones': (15,17)},
                            {'label':'i',
                            'phones': (17,18)
                                },
                            {'label':'guess',
                            'phones':(18,21)},
                            ],
                    'lines': [
                            {'label': '1',
                            'words':(0,3)},
                            {'label': '2',
                            'words':(3,6)},
                            {'label': '3',
                            'words': (6,8)}
                            ]
                    }
                }]
    return discourses


@pytest.fixture(scope='module')
def corpus_data_untimed():
    discourses = [{'name': 'test',
                    'data': {
                    'phones':[{'label': 'k'},
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
                    'words':[
                            {'label': 'cats',
                            'phones':(0,4)
                            },
                            {'label': 'are',
                            'phones':(4,6)},
                            {'label': 'cute',
                            'phones':(6,9)},
                            {'label': 'dogs',
                            'phones': (9,13)
                                },
                            {'label': 'are',
                            'phones': (13,15)},
                            {'label': 'too',
                            'phones': (15,17)},
                            {'label': 'i',
                            'phones': (17,18)
                                },
                            {'label':'guess',
                            'phones':(18,21)},
                            ],
                    'lines': [
                            {'label': '1',
                            'words':(0,3)},
                            {'label': '2',
                            'words':(3,6)},
                            {'label': '3',
                            'words': (6,8)}
                            ]
                    }
                }]
    return discourses


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
