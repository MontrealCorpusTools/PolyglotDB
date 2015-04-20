

import pytest

from annograph.config import session_scope

def test_lexicons_timed(timed_corpus):
    c = timed_corpus

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

def test_lexicons_untimed(untimed_corpus):
    c = untimed_corpus

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')

    with session_scope() as session:
        session.add(w)
        pt = c._type(session, 'phone')
        assert('.'.join(map(str,w.subarc('phone'))) == 'k.ae.t.s')

def test_lexicons_syllable_morpheme(syllable_morpheme_corpus):
    c = syllable_morpheme_corpus

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

def test_lexicons_srur(srur_corpus):
    c = srur_corpus

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
