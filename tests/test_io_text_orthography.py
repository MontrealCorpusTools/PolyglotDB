import os

from polyglotdb import CorpusContext
from polyglotdb.io import inspect_orthography


def test_load_spelling_no_ignore(graph_db, text_spelling_test_dir):
    spelling_path = os.path.join(text_spelling_test_dir, "text_spelling.txt")

    parser = inspect_orthography(spelling_path)

    with CorpusContext("spelling_no_ignore", **graph_db) as c:
        c.reset()
        c.load(parser, spelling_path)

        # assert(c.lexicon['ab'].frequency == 2


def test_load_spelling_directory(graph_db, text_spelling_test_dir):
    parser = inspect_orthography(text_spelling_test_dir)

    with CorpusContext("spelling_directory", **graph_db) as c:
        c.reset()
        c.load(parser, text_spelling_test_dir)


def test_load_spelling_ignore(graph_db, text_spelling_test_dir):
    spelling_path = os.path.join(text_spelling_test_dir, "text_spelling.txt")
    parser = inspect_orthography(spelling_path)
    parser.annotation_tiers[0].ignored_characters = {"'", "."}
    with CorpusContext("spelling_ignore", **graph_db) as c:
        c.reset()
        c.load(parser, spelling_path)

        # assert(c.lexicon['ab'].frequency == 3)
        # assert(c.lexicon['cabd'].frequency == 1)
