import os

import pytest

from polyglotdb import CorpusContext
from polyglotdb.exceptions import SubsetError


def test_encode_class(timed_config):
    with CorpusContext(timed_config) as g:
        label = "encoded_class"

        g.encode_class(["ae"], label)
        print(g.hierarchy.subset_types)

        q = g.query_graph(g.phone).filter(g.phone.subset == label)

        assert all(x.label == "ae" for x in q.all())

        q = g.query_graph(g.phone).filter(g.phone.subset != label)
        results = q.all()
        assert len(results) > 0
        assert all(x.label != "ae" for x in results)

        g.reset_class(label)
        print(g.hierarchy.subset_types)
        with pytest.raises(SubsetError):
            g.phone.filter_by_subset(label)


def test_feature_enrichment(timed_config, csv_test_dir):
    path = os.path.join(csv_test_dir, "timed_features.txt")
    with CorpusContext(timed_config) as c:
        c.enrich_inventory_from_csv(path)

        q = c.query_graph(c.phone).filter(c.phone.vowel_height == "lowhigh")

        q = q.columns(c.phone.label.column_name("label"))

        res = q.all()

        assert all(x["label"] == "ay" for x in res)

        q = c.query_graph(c.phone).filter(c.phone.place_of_articulation == "velar")

        q = q.columns(c.phone.label.column_name("label"))

        res = q.all()

        assert all(x["label"] in ["k", "g"] for x in res)


def test_reset_enrich_inventory(timed_config, csv_test_dir):
    path = os.path.join(csv_test_dir, "timed_features.txt")
    with CorpusContext(timed_config) as g:
        g.reset_inventory_csv(path)

        assert ("place_of_articulation", str) not in g.hierarchy.type_properties["phone"]

        statement = """MATCH (n:phone_type:{}) where n.place_of_articulation = 'velar' return count(n) as c""".format(
            g.cypher_safe_name
        )

        res = g.execute_cypher(statement)
        for r in res:
            assert r["c"] == 0
