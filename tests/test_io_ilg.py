import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import ILGWordMismatchError
from polyglotdb.io import inspect_ilg


def test_inspect_ilg(ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, "basic.txt")
    parser = inspect_ilg(basic_path)
    assert len(parser.annotation_tiers) == 2
    assert parser.annotation_tiers[1].trans_delimiter == "."


def test_inspect_ilg_directory(ilg_test_dir):
    parser = inspect_ilg(ilg_test_dir)
    assert len(parser.annotation_tiers) == 2


def test_ilg_basic(graph_db, ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, "basic.txt")

    parser = inspect_ilg(basic_path)
    with CorpusContext("basic_ilg", **graph_db) as c:
        c.reset()
        c.load(parser, basic_path)
        # assert(c.lexicon['a'].frequency == 2)


def test_ilg_mismatched(graph_db, ilg_test_dir):
    mismatched_path = os.path.join(ilg_test_dir, "mismatched.txt")
    basic_path = os.path.join(ilg_test_dir, "basic.txt")

    parser = inspect_ilg(basic_path)

    with CorpusContext("mismatch", **graph_db) as c:
        c.reset()
        with pytest.raises(ILGWordMismatchError):
            c.load(parser, mismatched_path)
