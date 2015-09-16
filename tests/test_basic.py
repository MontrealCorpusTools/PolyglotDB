import os
import pytest

from annograph.sql.classes import Corpus

from annograph.sql.config import session_scope

from annograph.io.io import add_discourse_graph

@pytest.mark.xfail
def test_corpus_timed(timed_corpus):
    c = timed_corpus

    with session_scope() as session:
        t = c._wordtype(session)
        pt = c._type(session, 'phone')

        assert(t.type_label == 'word')

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')

@pytest.mark.xfail
def test_corpus_untimed(untimed_corpus):
    c = untimed_corpus

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')

@pytest.mark.xfail
def test_corpus_syllable_morpheme(syllable_morpheme_corpus):
    c = syllable_morpheme_corpus

@pytest.mark.xfail
def test_corpus_srur(srur_corpus):
    c = srur_corpus

    w = c.find('cats')
    assert(w.annotation.annotation_label == 'cats')

