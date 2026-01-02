import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import GraphQueryError
from polyglotdb.io import inspect_textgrid
from polyglotdb.io.types.parsing import OrthographyTier, TobiTier


def test_tobi(textgrid_test_dir):
    path = os.path.join(textgrid_test_dir, "tobi.TextGrid")
    parser = inspect_textgrid(path)
    assert isinstance(parser.annotation_tiers[0], TobiTier)
    assert isinstance(parser.annotation_tiers[1], OrthographyTier)


def test_load(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, "phone_word.TextGrid")
    with CorpusContext("test_textgrid", **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_tiers[1].linguistic_type = "word"
        parser.annotation_tiers[2].ignored = True
        parser.hierarchy["word"] = None
        parser.hierarchy["phone"] = "word"
        print([(x.linguistic_type, x.name) for x in parser.annotation_tiers])
        c.load(parser, path)


def test_load_pronunciation_ignore(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, "pronunc_variants_corpus.TextGrid")
    with CorpusContext("test_pronunc", **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_tiers[1].ignored = True
        parser.annotation_tiers[2].ignored = True
        c.load(parser, path)

        with pytest.raises(GraphQueryError):
            q = c.query_graph(c.actualPron)
            q.all()


def test_load_pronunciation(textgrid_test_dir, graph_db):
    path = os.path.join(textgrid_test_dir, "pronunc_variants_corpus.TextGrid")

    with CorpusContext("test_pronunc", **graph_db) as c:
        c.reset()
        parser = inspect_textgrid(path)
        parser.annotation_tiers[2].type_property = False
        c.load(parser, path)

        q = c.query_graph(c.word).filter(c.word.label == "probably")
        q = q.order_by(c.word.begin)
        q = q.columns(
            c.word.label,
            c.word.dictionaryPron.column_name("dict_pron"),
            c.word.actualPron.column_name("act_pron"),
        )
        results = q.all()
        assert results[0]["dict_pron"] == "p.r.aa.b.ah.b.l.iy"
        assert results[0]["act_pron"] == "p.r.aa.b.ah.b.l.iy"


def test_word_transcription(graph_db, textgrid_test_dir):
    with CorpusContext("discourse_textgrid", **graph_db) as c:
        c.reset()
        path = os.path.join(textgrid_test_dir, "acoustic_corpus.TextGrid")
        parser = inspect_textgrid(path)
        c.load(parser, path)
        assert c.hierarchy.has_type_property("word", "transcription")
