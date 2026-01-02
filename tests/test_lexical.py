import pytest

from polyglotdb import CorpusContext


def test_lexicon_enrichment(timed_config, timed_lexicon_enrich_file):
    with CorpusContext(timed_config) as c:
        c.enrich_lexicon_from_csv(timed_lexicon_enrich_file)

        q = c.query_graph(c.word).filter(c.word.neighborhood_density < 10)

        q = q.columns(c.word.label.column_name("label"))

        res = q.all()

        assert all(x["label"] == "guess" for x in res)

        q = c.query_graph(c.word).filter(c.word.label == "i")

        res = q.all()

        assert res[0]["frequency"] == 150
        assert res[0]["part_of_speech"] == "PRP"
        assert res[0]["neighborhood_density"] == 17

        q = c.query_graph(c.word).filter(c.word.label == "cute")

        res = q.all()

        assert res[0]["frequency"] is None
        assert res[0]["part_of_speech"] == "JJ"
        assert res[0]["neighborhood_density"] == 14

        # currently unsupported
        levels = c.query_metadata(c.word).levels(c.word.part_of_speech)
        assert set(levels) == {None, "NN", "VB", "JJ", "IN", "PRP"}


def test_reset_enrich_lexicon(timed_config, timed_lexicon_enrich_file):
    with CorpusContext(timed_config) as g:
        g.reset_lexicon_csv(timed_lexicon_enrich_file)

        assert ("frequency", int) not in g.hierarchy.type_properties["word"]

        statement = """MATCH (n:word_type:{}) where n.frequency > 0 return count(n) as c""".format(
            g.cypher_safe_name
        )

        res = g.execute_cypher(statement)
        for r in res:
            assert r["c"] == 0
