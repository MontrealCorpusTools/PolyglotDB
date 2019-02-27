import pytest
import os
import sys

from polyglotdb.io import inspect_ilg

from polyglotdb.io.helper import guess_type

from polyglotdb.exceptions import DelimiterError, ILGWordMismatchError

from polyglotdb import CorpusContext


def test_inspect_ilg(ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, 'basic.txt')
    parser = inspect_ilg(basic_path)
    assert (len(parser.annotation_tiers) == 2)
    assert (parser.annotation_tiers[1].trans_delimiter == '.')


def test_inspect_ilg_directory(ilg_test_dir):
    parser = inspect_ilg(ilg_test_dir)
    assert (len(parser.annotation_tiers) == 2)


@pytest.mark.xfail
def test_export_ilg(graph_db, export_test_dir):
    export_path = os.path.join(export_test_dir, 'export_ilg.txt')
    with CorpusContext('untimed', **graph_db) as c:
        export_discourse_ilg(c, 'test', export_path,
                             annotations=['label', 'transcription'], words_per_line=3)
    expected_lines = ['cats are cute',
                      'k.ae.t.s aa.r k.uw.t',
                      'dogs are too',
                      'd.aa.g.z aa.r t.uw',
                      'i guess',
                      'ay g.eh.s']
    with open(export_path, 'r') as f:
        for i, line in enumerate(f):
            assert (line.strip() == expected_lines[i])


def test_ilg_basic(graph_db, ilg_test_dir):
    basic_path = os.path.join(ilg_test_dir, 'basic.txt')

    parser = inspect_ilg(basic_path)
    with CorpusContext('basic_ilg', **graph_db) as c:
        c.reset()
        c.load(parser, basic_path)
        # assert(c.lexicon['a'].frequency == 2)


def test_ilg_mismatched(graph_db, ilg_test_dir):
    mismatched_path = os.path.join(ilg_test_dir, 'mismatched.txt')
    basic_path = os.path.join(ilg_test_dir, 'basic.txt')

    parser = inspect_ilg(basic_path)

    with CorpusContext('mismatch', **graph_db) as c:
        c.reset()
        with pytest.raises(ILGWordMismatchError):
            c.load(parser, mismatched_path)
