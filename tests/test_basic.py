import os
import pytest

from annograph.classes import Corpus

from annograph.config import session_scope

def test_corpus_timed(test_dir, corpus_data_timed):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_timed.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_timed)

    with session_scope() as session:
        t = c._wordtype(session)
        pt = c._type(session, 'phone')

        assert(t.type_label == 'word')

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')

    with session_scope() as session:
        session.add(w)

        pt = c._type(session, 'phone')
        assert(w.subarc_sql(session, pt).first()[0] == 'k.ae.t.s')
        assert('.'.join(map(str,w.subarc('phone'))) == 'k.ae.t.s')
    c._generate_frequency_table()
    c._get_transitive_closures( 'word', 'phone')
    wordlist = c.get_wordlist()
    print(wordlist)
    #assert(False)

def test_corpus_untimed(test_dir, corpus_data_untimed):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_untimed.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_untimed)

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')


    with session_scope() as session:
        session.add(w)
        pt = c._type(session, 'phone')
        assert('.'.join(map(str,w.subarc('phone'))) == 'k.ae.t.s')

def test_corpus_syllable_morpheme(test_dir, corpus_data_stress_morpheme):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_syllable_morpheme.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_stress_morpheme)

    with session_scope() as session:
        pt = c._type(session, 'phone')
        sylt = c._type(session, 'syllable')
        mort = c._type(session, 'morpheme')
        qs = c._find(session, '(b.aa.k)', 'syllable')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'b.aa.k')
        qs = c._find(session, '(s.ah.z)', 'syllable')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 's.ah.z')
        qs = c._find(session, '(aa.r)', 'syllable')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'aa.r')
        qs = c._find(session, '(f.ao.r)', 'syllable')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'f.ao.r')
        qs = c._find(session, '(p.ae)', 'syllable')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'p.ae')
        qs = c._find(session, '(k.ih.ng)', 'syllable')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'k.ih.ng')
        qs = c._find(session, 'box', 'morpheme')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'b.aa.k.s')
        qs = c._find(session, 'PL', 'morpheme')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'ah.z')
        qs = c._find(session, 'PROG', 'morpheme')
        assert('.'.join(map(str,qs[0].subarc('phone'))), 'ih.ng')

def test_corpus_srur(test_dir, corpus_data_ur_sr):
    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_ur_sr.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_ur_sr)

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')

    with session_scope() as session:
        session.add(w)
        pt = c._type(session, 'sr')
        assert('.'.join(map(str,w.subarc('sr'))) == 'k.ae.s')

        pt = c._type(session, 'ur')
        assert('.'.join(map(str,w.subarc('ur'))) == 'k.ae.t.s')

    w = c.find('dogs')
    assert(w.annotation.annotation_label == 'dogs')

    with session_scope() as session:
        session.add(w)
        pt = c._type(session, 'sr')
        assert('.'.join(map(str,w.subarc('sr'))) == 'd.aa.g.ah.z')

        pt = c._type(session, 'ur')
        assert('.'.join(map(str,w.subarc('ur'))) == 'd.aa.g.z')
