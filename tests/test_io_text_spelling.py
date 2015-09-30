
import pytest
import os

from polyglotdb.io.text_spelling import (load_discourse_spelling,
                                                load_directory_spelling,
                                                inspect_discourse_spelling,
                                                export_discourse_spelling)

from polyglotdb.exceptions import DelimiterError

from polyglotdb.corpus import CorpusContext


def test_load_spelling_no_ignore(graph_db, text_spelling_test_dir):
    spelling_path = os.path.join(text_spelling_test_dir, 'text_spelling.txt')

    with CorpusContext(corpus_name = 'spelling_no_ignore', **graph_db) as c:
        c.reset()
        load_discourse_spelling(c, spelling_path)

    assert(c.lexicon['ab'].frequency == 2)

def test_load_spelling_directory(graph_db, text_spelling_test_dir):

    with CorpusContext(corpus_name = 'spelling_directory', **graph_db) as c:
        load_directory_spelling(c, text_spelling_test_dir)

def test_export_spelling(graph_db, export_test_dir):

    export_path = os.path.join(export_test_dir, 'export_spelling.txt')
    with CorpusContext(corpus_name = 'spelling_no_ignore', **graph_db) as c:
        export_discourse_spelling(c, 'text_spelling', export_path, words_per_line = 10)

    with open(export_path,'r') as f:
        assert(f.read() == 'ab cab\'d ad ab ab.')


def test_load_spelling_ignore(graph_db, text_spelling_test_dir):
    spelling_path = os.path.join(text_spelling_test_dir, 'text_spelling.txt')
    a = inspect_discourse_spelling(spelling_path)
    a[0].ignored_characters = set(["'",'.'])
    with CorpusContext(corpus_name = 'spelling_ignore', **graph_db) as c:
        c.reset()
        load_discourse_spelling(c, spelling_path, a)

    assert(c.lexicon['ab'].frequency == 3)
    assert(c.lexicon['cabd'].frequency == 1)

