import hashlib
from collections import Counter, defaultdict
from collections.abc import Callable

import pytest

from polyglotdb import CorpusConfig, CorpusContext
from polyglotdb.syllabification.match_onset import MatchOnset


@pytest.fixture
def make_timed_config(graph_db, corpus_data_timed):
    def _make_timed_config():
        config = CorpusConfig("timed", **graph_db)
        with CorpusContext(config) as c:
            c.reset()
            c.add_types(*corpus_data_timed.types("timed"))
            c.initialize_import(
                corpus_data_timed.speakers,
                corpus_data_timed.token_headers,
                corpus_data_timed.hierarchy.subannotations,
            )
            c.add_discourse(corpus_data_timed)
            c.finalize_import(
                corpus_data_timed.speakers,
                corpus_data_timed.token_headers,
                corpus_data_timed.hierarchy,
            )
        return config

    return _make_timed_config


def _canonical_signatures(nodes, rels, iterations=3) -> dict:
    """Generate a canonical signature for each node in the graph.

    A signature takes into account the node's labels, properties, and relationships.

    Parameters
    ----------
    nodes
        List of (id, labels, props).
    rels
        List of (start_id, end_id, type, props).
    iterations
        Number of iterations to run the signature algorithm.

    Returns
    -------
        A dictionary mapping node IDs to their canonical signatures.
    """
    sig = {}
    for node_id, labels, props in nodes:
        base = repr((sorted(labels), sorted(props.items())))
        sig[node_id] = hashlib.sha256(base.encode()).hexdigest()

    adjacency = defaultdict(list)
    for start, end, rtype, rprops in rels:
        key = repr((rtype, sorted(rprops.items())))
        adjacency[start].append(("out", key, end))
        adjacency[end].append(("in", key, start))

    for _ in range(iterations):
        new_sig = {}
        for node_id in sig:
            neighbour_part = sorted(
                f"{direction}:{key}:{sig[other]}" for direction, key, other in adjacency[node_id]
            )
            combined = sig[node_id] + "|" + "|".join(neighbour_part)
            new_sig[node_id] = hashlib.sha256(combined.encode()).hexdigest()
        sig = new_sig
    return sig


def make_canonical_signatures(corpus_context: CorpusContext) -> dict:
    nodes = corpus_context.graph_driver.execute_query(
        """
        MATCH (n)
        RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props
    """
    ).records
    nodes_tuples = []
    for node in nodes:
        # Remove volatile properties
        props = {
            key: value for key, value in node["props"].items() if key not in ["id", "line", "word"]
        }
        nodes_tuples.append((node["id"], node["labels"], props))

    rels = corpus_context.graph_driver.execute_query(
        """
        MATCH (a)-[r]->(b)
        RETURN id(a) AS start, id(b) AS end, type(r) AS type, properties(r) AS props
    """
    ).records
    rels_tuples = [(rel["start"], rel["end"], rel["type"], rel["props"]) for rel in rels]
    return _canonical_signatures(nodes_tuples, rels_tuples)


def test_encode_syllables_v2(make_timed_config: Callable[[], CorpusConfig]):
    """Equivalence test the function against the existing encode_syllables impl."""
    syllabics = ["ae", "aa", "uw", "ay", "eh"]

    sig_v1 = {}
    sig_v2 = {}

    timed_config = make_timed_config()
    with CorpusContext(timed_config) as c:
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables()
        sig_v1 = make_canonical_signatures(c)

    # Reset corpus
    timed_config = make_timed_config()
    with CorpusContext(timed_config) as c:
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables_v2(MatchOnset.from_corpus(c))
        sig_v2 = make_canonical_signatures(c)

    # Because node ids are not stabble, we only compare the signatures themselves
    assert Counter(sig_v1.values()) == Counter(sig_v2.values())
