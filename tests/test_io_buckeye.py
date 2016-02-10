
import pytest
import os

from polyglotdb.io import inspect_buckeye

from polyglotdb.io.parsers.buckeye import read_phones, read_words

from polyglotdb.corpus import CorpusContext

def test_load_phones(buckeye_test_dir):
    expected_phones = [('{B_TRANS}',0.0, 2.609000),
                            ('IVER',2.609000, 2.714347),
                            ('eh',2.714347, 2.753000),
                            ('s',2.753000, 2.892000),
                            ('IVER',2.892000, 3.206890),
                            ('dh',3.206890, 3.244160),
                            ('ae',3.244160, 3.327000),
                            ('s',3.327000, 3.377192),
                            ('s',3.377192, 3.438544),
                            ('ae',3.438544, 3.526272),
                            ('tq',3.526272, 3.614398),
                            ('VOCNOISE',3.614398, 3.673454),
                            ('ah',3.673454, 3.718614),
                            ('w',3.718614, 3.771112),
                            ('ah',3.771112, 3.851000),
                            ('dx',3.851000, 3.881000),
                            ('eh',3.881000, 3.941000),
                            ('v',3.941000, 4.001000),
                            ('er',4.001000, 4.036022),
                            ('ey',4.036022, 4.111000),
                            ('k',4.111000, 4.246000),
                            ('ao',4.246000, 4.326000),
                            ('l',4.326000, 4.369000),
                            ('ah',4.369000, 4.443707),
                            ('t',4.443707, 4.501000),
                            ]
    phones = read_phones(os.path.join(buckeye_test_dir,'test.phones'))
    for i,p in enumerate(expected_phones):
        assert(p == phones[i])

def test_load_words(buckeye_test_dir):
    words = read_words(os.path.join(buckeye_test_dir, 'test.words'))
    expected_words = [{'spelling':'{B_TRANS}','begin':0,'end':2.609000,'transcription':None,'surface_transcription':None,'category':None},
        {'spelling':'<IVER>','begin':2.609000,'end':2.714347,'transcription':None,'surface_transcription':None,'category':None},
        {'spelling':'that\'s','begin':2.714347,'end':2.892096,'transcription':['dh', 'ae', 't', 's'],'surface_transcription':['eh', 's'],'category':'DT_VBZ'},
        {'spelling':'<IVER>','begin':2.892096,'end':3.206317,'transcription':None,'surface_transcription':None,'category':None},
        {'spelling':'that\'s','begin':3.206317,'end':3.377192,'transcription':['dh', 'ae', 't', 's'],'surface_transcription':['dh','ae','s'],'category':'DT_VBZ'},
        {'spelling':'that','begin':3.377192,'end':3.614398,'transcription':['dh','ae','t'],'surface_transcription':['s','ae','tq'],'category':'IN'},
        {'spelling':'<VOCNOISE>','begin':3.614398,'end':3.673454,'transcription':None,'surface_transcription':None,'category':None},
        {'spelling':'whatever','begin':3.673454,'end':4.036022,'transcription':['w','ah','t','eh','v','er'],'surface_transcription':['ah','w','ah','dx','eh','v','er'],'category':'WDT'},
        {'spelling':'they','begin':4.036022,'end':4.111000,'transcription':['dh','ey'],'surface_transcription':['ey'],'category':'PRP'},
        {'spelling':'call','begin':4.111000,'end':4.369000,'transcription':['k','aa','l'],'surface_transcription':['k','ao','l'],'category':'VBP'},
        {'spelling':'it','begin':4.369000,'end':4.501000,'transcription':['ih','t'],'surface_transcription':['ah','t'],'category':'PRP'}]
    for i,w in enumerate(expected_words):
        assert(w == words[i])

def test_load_discourse_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('discourse_buckeye', **graph_db) as c:
        c.reset()
        word_path = os.path.join(buckeye_test_dir,'test.words')
        parser = inspect_buckeye(word_path)
        c.load(parser, word_path)

        q = c.query_graph(c.surface_transcription).filter(c.surface_transcription.label == 's')
        assert(q.count() == 3)

        q = q.columns(c.surface_transcription.speaker.name.column_name('speaker'))
        print(q.cypher())
        results = q.all()
        print(results)
        assert(all(x.speaker == 'tes' for x in results))

def test_load_directory_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        c.reset()
        parser = inspect_buckeye(buckeye_test_dir)
        c.load(parser, buckeye_test_dir)

        q = c.query_graph(c.surface_transcription).filter(c.surface_transcription.label == 's')
        assert(q.count() == 3)

        q = q.columns(c.surface_transcription.speaker.name.column_name('speaker'))
        print(q.cypher())
        results = q.all()
        print(results)
        assert(all(x.speaker == 'tes' for x in results))
