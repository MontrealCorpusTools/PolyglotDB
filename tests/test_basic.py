import os

from annograph.classes import Corpus

TEST_DIR = 'tests/data'

def test_corpus_timed(corpus_data_timed):

    c = Corpus('sqlite:///'+ os.path.join(TEST_DIR,'generated','test_timed.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_timed)

def test_corpus_untimed(corpus_data_untimed):

    c = Corpus('sqlite:///'+ os.path.join(TEST_DIR,'generated','test_untimed.db'))
    c.initial_setup()
    c.add_discourses(corpus_data_untimed)
