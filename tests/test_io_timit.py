
import pytest
import os

from polyglotdb.io.standards.timit import (read_phones, read_words,
                            BaseAnnotation,
                            timit_to_data,
                            load_discourse_timit,
                            load_directory_timit)

from polyglotdb.corpus import CorpusContext

def test_load_phones(timit_test_dir):
    expected_phones = [BaseAnnotation('h#',0, 2400 / 16000),
                            BaseAnnotation('sh',2400 / 16000, 4260/ 16000),
                            BaseAnnotation('iy',4260 / 16000,5480 / 16000),
                            BaseAnnotation('hv',5480 / 16000,6516 / 16000),
                            BaseAnnotation('ae',6516 / 16000,8856 / 16000),
                            BaseAnnotation('dcl',8856 / 16000,9610 / 16000),
                            BaseAnnotation('d',9610 / 16000,9859 / 16000),
                            BaseAnnotation('y',9859 / 16000,10639 / 16000),
                            BaseAnnotation('axr',10639 / 16000,12200 / 16000),
                            BaseAnnotation('dcl',12200 / 16000,13380 / 16000),
                            BaseAnnotation('d',13380 / 16000,13540 / 16000),
                            BaseAnnotation('aa',13540 / 16000,15426 / 16000),
                            BaseAnnotation('r',15426 / 16000, 16440/ 16000),
                            BaseAnnotation('kcl',16440 / 16000,17330 / 16000),
                            BaseAnnotation('k',17330 / 16000,17796 / 16000),
                            BaseAnnotation('s',17796 / 16000,19860 / 16000),
                            BaseAnnotation('ux',19860 / 16000,21880 / 16000),
                            BaseAnnotation('tcl',21880 / 16000,22180 / 16000),
                            BaseAnnotation('t',22180 / 16000,22511 / 16000),
                            BaseAnnotation('q',22511 / 16000,23436 / 16000),
                            BaseAnnotation('ih',23436 / 16000,24229 / 16000),
                            BaseAnnotation('n', 24229/ 16000,25400 / 16000),
                            BaseAnnotation('gcl',25400 / 16000,26130 / 16000),
                            BaseAnnotation('g',26130 / 16000,26960 / 16000),
                            BaseAnnotation('r',26960 / 16000,27750 / 16000),
                            BaseAnnotation('iy',27750 / 16000,29368 / 16000),
                            BaseAnnotation('s',29368 / 16000,31140 / 16000),
                            BaseAnnotation('iy',31140 / 16000,32584 / 16000),
                            BaseAnnotation('w', 32584/ 16000,33796 / 16000),
                            BaseAnnotation('aa',33796 / 16000,36845 / 16000),
                            BaseAnnotation('sh', 36845/ 16000,38417 / 16000),
                            BaseAnnotation('epi',38417 / 16000,38833 / 16000),
                            BaseAnnotation('w', 38833/ 16000,39742 / 16000),
                            BaseAnnotation('ao',39742 / 16000,41560 / 16000),
                            BaseAnnotation('dx', 41560/ 16000,41934 / 16000),
                            BaseAnnotation('axr',41934 / 16000,43730 / 16000),
                            BaseAnnotation('q', 43730/ 16000,45067 / 16000),
                            BaseAnnotation('aa',45067 / 16000,47026 / 16000),
                            BaseAnnotation('l',47026 / 16000,48200 / 16000),
                            BaseAnnotation('y', 48200/ 16000,49996 / 16000),
                            BaseAnnotation('ix',49996 / 16000,51876 / 16000),
                            BaseAnnotation('axr', 51876/ 16000,53756 / 16000),
                            BaseAnnotation('h#',53756 / 16000,55840 / 16000),
                            ]
    phones = read_phones(os.path.join(timit_test_dir,'test.PHN'))
    for i,p in enumerate(expected_phones):
        assert(p == phones[i])

def test_load_words(timit_test_dir):
    words = read_words(os.path.join(timit_test_dir, 'test.WRD'))
    expected_words = [{'spelling':'she','begin': 2400 / 16000,'end': 5480 / 16000},
        {'spelling':'had','begin': 5480 / 16000,'end': 9859 / 16000,},
        {'spelling':'your','begin': 9859 / 16000,'end': 12200 / 16000,},
        {'spelling':'dark','begin': 12200 / 16000,'end': 17796 / 16000},
        {'spelling':'suit','begin': 17796 / 16000,'end': 22511 / 16000},
        {'spelling':'in','begin': 22511 / 16000,'end': 25400 / 16000},
        {'spelling':'greasy','begin': 25400 / 16000,'end': 32584 / 16000},
        {'spelling':'wash','begin': 32584 / 16000,'end': 38417 / 16000},
        {'spelling':'water','begin': 38833 / 16000,'end': 43730 / 16000},
        {'spelling':'all','begin': 45067 / 16000,'end': 48200 / 16000},
        {'spelling':'year','begin': 48200 / 16000,'end': 53756 / 16000}]
    for i,w in enumerate(expected_words):
        assert(w == words[i])

def test_load_discourse_timit(graph_db, timit_test_dir):
    with CorpusContext(corpus_name = 'discourse_timit', **graph_db) as c:
        c.reset()
        load_discourse_timit(c,os.path.join(timit_test_dir,'test.WRD'),
                            os.path.join(timit_test_dir,'test.PHN'))

        q = c.query_graph(c.surface_transcription).filter(c.surface_transcription.label == 'dcl')
        assert(q.count() == 2)

def test_load_directory_timit(graph_db, timit_test_dir):
    with CorpusContext(corpus_name = 'directory_timit', **graph_db) as c:
        c.reset()
        load_directory_timit(c, timit_test_dir)

        q = c.query_graph(c.surface_transcription).filter(c.surface_transcription.label == 'dcl')
        assert(q.count() == 2)
