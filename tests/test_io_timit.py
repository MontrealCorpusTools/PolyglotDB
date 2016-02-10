
import pytest
import os

from polyglotdb.io import inspect_timit

from polyglotdb.io.parsers.timit import read_phones, read_words

from polyglotdb.corpus import CorpusContext

def test_load_phones(timit_test_dir):
    expected_phones = [('h#',0, 2400 / 16000),
                            ('sh',2400 / 16000, 4260/ 16000),
                            ('iy',4260 / 16000,5480 / 16000),
                            ('hv',5480 / 16000,6516 / 16000),
                            ('ae',6516 / 16000,8856 / 16000),
                            ('dcl',8856 / 16000,9610 / 16000),
                            ('d',9610 / 16000,9859 / 16000),
                            ('y',9859 / 16000,10639 / 16000),
                            ('axr',10639 / 16000,12200 / 16000),
                            ('dcl',12200 / 16000,13380 / 16000),
                            ('d',13380 / 16000,13540 / 16000),
                            ('aa',13540 / 16000,15426 / 16000),
                            ('r',15426 / 16000, 16440/ 16000),
                            ('kcl',16440 / 16000,17330 / 16000),
                            ('k',17330 / 16000,17796 / 16000),
                            ('s',17796 / 16000,19860 / 16000),
                            ('ux',19860 / 16000,21880 / 16000),
                            ('tcl',21880 / 16000,22180 / 16000),
                            ('t',22180 / 16000,22511 / 16000),
                            ('q',22511 / 16000,23436 / 16000),
                            ('ih',23436 / 16000,24229 / 16000),
                            ('n', 24229/ 16000,25400 / 16000),
                            ('gcl',25400 / 16000,26130 / 16000),
                            ('g',26130 / 16000,26960 / 16000),
                            ('r',26960 / 16000,27750 / 16000),
                            ('iy',27750 / 16000,29368 / 16000),
                            ('s',29368 / 16000,31140 / 16000),
                            ('iy',31140 / 16000,32584 / 16000),
                            ('w', 32584/ 16000,33796 / 16000),
                            ('aa',33796 / 16000,36845 / 16000),
                            ('sh', 36845/ 16000,38417 / 16000),
                            ('epi',38417 / 16000,38833 / 16000),
                            ('w', 38833/ 16000,39742 / 16000),
                            ('ao',39742 / 16000,41560 / 16000),
                            ('dx', 41560/ 16000,41934 / 16000),
                            ('axr',41934 / 16000,43730 / 16000),
                            ('q', 43730/ 16000,45067 / 16000),
                            ('aa',45067 / 16000,47026 / 16000),
                            ('l',47026 / 16000,48200 / 16000),
                            ('y', 48200/ 16000,49996 / 16000),
                            ('ix',49996 / 16000,51876 / 16000),
                            ('axr', 51876/ 16000,53756 / 16000),
                            ('h#',53756 / 16000,55840 / 16000)]
    phones = read_phones(os.path.join(timit_test_dir,'test.PHN'))
    for i,p in enumerate(expected_phones):
        assert(p == phones[i])

def test_load_words(timit_test_dir):
    words = read_words(os.path.join(timit_test_dir, 'test.WRD'))
    expected_words = [
        {'spelling':'sil','begin': 0,'end': 2400 / 16000},
        {'spelling':'she','begin': 2400 / 16000,'end': 5480 / 16000},
        {'spelling':'had','begin': 5480 / 16000,'end': 9859 / 16000,},
        {'spelling':'your','begin': 9859 / 16000,'end': 12200 / 16000,},
        {'spelling':'dark','begin': 12200 / 16000,'end': 17796 / 16000},
        {'spelling':'suit','begin': 17796 / 16000,'end': 22511 / 16000},
        {'spelling':'in','begin': 22511 / 16000,'end': 25400 / 16000},
        {'spelling':'greasy','begin': 25400 / 16000,'end': 32584 / 16000},
        {'spelling':'wash','begin': 32584 / 16000,'end': 38417 / 16000},
        {'spelling': 'sil','begin': 38417 / 16000, 'end':38833 / 16000},
        {'spelling':'water','begin': 38833 / 16000,'end': 43730 / 16000},
        {'spelling': 'sil','begin': 43730 / 16000, 'end':45067 / 16000},
        {'spelling':'all','begin': 45067 / 16000,'end': 48200 / 16000},
        {'spelling':'year','begin': 48200 / 16000,'end': 53756 / 16000}]
    for i,w in enumerate(expected_words):
        assert(w == words[i])

def test_load_discourse_timit(graph_db, timit_test_dir):
    word_path = os.path.join(timit_test_dir,'test.WRD')
    with CorpusContext('discourse_timit', **graph_db) as c:
        c.reset()

        parser = inspect_timit(word_path)
        c.load(parser, word_path)

        q = c.query_graph(c.surface_transcription).filter(c.surface_transcription.label == 'dcl')
        assert(q.count() == 2)

        q = q.columns(c.surface_transcription.speaker.name.column_name('speaker'))
        results = q.all()
        assert(all(x.speaker == 'timit' for x in results))

def test_load_directory_timit(graph_db, timit_test_dir):
    parser = inspect_timit(timit_test_dir)
    with CorpusContext('directory_timit', **graph_db) as c:
        c.reset()
        c.load(parser, timit_test_dir)

        q = c.query_graph(c.surface_transcription).filter(c.surface_transcription.label == 'dcl')
        assert(q.count() == 2)

        q = q.columns(c.surface_transcription.speaker.name.column_name('speaker'))
        results = q.all()
        assert(all(x.speaker == 'timit' for x in results))
