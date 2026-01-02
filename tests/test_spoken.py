import os

import pytest

from polyglotdb import CorpusContext


def test_speaker_enrichment_csv(fave_corpus_config, csv_test_dir):
    path = os.path.join(csv_test_dir, "fave_speaker_info.txt")
    with CorpusContext(fave_corpus_config) as c:
        c.enrich_speakers_from_csv(path)

        q = c.query_graph(c.phone).filter(c.phone.speaker.is_interviewer == True)  # noqa

        q = q.columns(
            c.phone.label.column_name("label"),
            c.phone.speaker.name.column_name("speaker"),
        )

        res = q.all()

        assert all(x["speaker"] == "Interviewer" for x in res)


def test_reset_enrich_speaker(fave_corpus_config, csv_test_dir):
    path = os.path.join(csv_test_dir, "fave_speaker_info.txt")
    with CorpusContext(fave_corpus_config) as g:
        g.reset_speaker_csv(path)

        assert ("is_interviewer", bool) not in g.hierarchy.speaker_properties

        statement = (
            """MATCH (n:Speaker:{}) where n.is_interviewer = True return count(n) as c""".format(
                g.cypher_safe_name
            )
        )

        res = g.execute_cypher(statement)
        for r in res:
            assert r["c"] == 0


def test_discourse_enrichment(fave_corpus_config, csv_test_dir):
    path = os.path.join(csv_test_dir, "fave_discourse_info.txt")
    with CorpusContext(fave_corpus_config) as c:
        c.enrich_discourses_from_csv(path)

        q = c.query_graph(c.phone).filter(c.phone.discourse.noise_level == "high")

        q = q.columns(
            c.phone.label.column_name("label"),
            c.phone.discourse.name.column_name("discourse"),
        )

        res = q.all()

        assert all(x["discourse"] == "fave_test" for x in res)


def test_reset_enrich_discourse(fave_corpus_config, csv_test_dir):
    path = os.path.join(csv_test_dir, "fave_discourse_info.txt")
    with CorpusContext(fave_corpus_config) as g:
        g.reset_discourse_csv(path)

        assert ("noise_level", str) not in g.hierarchy.discourse_properties

        statement = (
            """MATCH (n:Speaker:{}) where n.noise_level = 'high' return count(n) as c""".format(
                g.cypher_safe_name
            )
        )

        res = g.execute_cypher(statement)
        for r in res:
            assert r["c"] == 0
