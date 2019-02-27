import pytest
import os

from polyglotdb.io import inspect_orthography

from polyglotdb.exceptions import DelimiterError

from polyglotdb import CorpusContext


def test_load_spelling_no_ignore(graph_db, text_spelling_test_dir):
    spelling_path = os.path.join(text_spelling_test_dir, 'text_spelling.txt')

    parser = inspect_orthography(spelling_path)

    with CorpusContext('spelling_no_ignore', **graph_db) as c:
        c.reset()
        c.load(parser, spelling_path)

        # assert(c.lexicon['ab'].frequency == 2)


def test_load_spelling_directory(graph_db, text_spelling_test_dir):
    parser = inspect_orthography(text_spelling_test_dir)

    with CorpusContext('spelling_directory', **graph_db) as c:
        c.reset()
        c.load(parser, text_spelling_test_dir)


@pytest.mark.xfail
def test_export_spelling(graph_db, export_test_dir):
    export_path = os.path.join(export_test_dir, 'export_spelling.txt')
    with CorpusContext('spelling_no_ignore', **graph_db) as c:
        export_discourse_spelling(c, 'text_spelling', export_path, words_per_line=10)

    with open(export_path, 'r') as f:
        assert (f.read() == 'ab cab\'d ad ab ab.')


def test_load_spelling_ignore(graph_db, text_spelling_test_dir):
    spelling_path = os.path.join(text_spelling_test_dir, 'text_spelling.txt')
    parser = inspect_orthography(spelling_path)
    parser.annotation_tiers[0].ignored_characters = set(["'", '.'])
    with CorpusContext('spelling_ignore', **graph_db) as c:
        c.reset()
        c.load(parser, spelling_path)

        # assert(c.lexicon['ab'].frequency == 3)
        # assert(c.lexicon['cabd'].frequency == 1)
