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
        assert('.'.join(map(str,w.subarc(pt))) == 'k.ae.t')





def test_corpus_untimed(test_dir, corpus_data_untimed):

    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_untimed.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_untimed)

@pytest.mark.xfail
def test_corpus_srur(test_dir, corpus_data_ur_sr):

    c = Corpus('sqlite:///'+ os.path.join(test_dir,'generated','test_untimed.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_ur_sr)
