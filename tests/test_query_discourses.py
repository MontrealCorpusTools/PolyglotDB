from polyglotdb import CorpusContext


def test_discourse_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_discourses().filter(g.discourse.name == "acoustic_corpus")
        q = q.columns(g.discourse.name.column_name("discourse"))
        results = q.all()
        assert len(results) == 1
        assert results[0]["discourse"] == "acoustic_corpus"


def test_discourse_speaker_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_discourses().filter(g.discourse.name == "acoustic_corpus")
        q = q.columns(
            g.discourse.name.column_name("discourse"),
            g.discourse.speakers.name.column_name("speakers"),
            g.discourse.speakers.channel.column_name("channels"),
        )
        print(q.cypher())
        results = q.all()
        assert len(results) == 1
        assert results[0]["discourse"] == "acoustic_corpus"
        assert results[0]["speakers"] == ["unknown"]
        assert results[0]["channels"] == [0]
