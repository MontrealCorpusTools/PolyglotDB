from polyglotdb import CorpusContext


def test_speaker_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_speakers().filter(g.speaker.name == "unknown")
        q = q.columns(g.speaker.name.column_name("speaker"))
        results = q.all()
        assert len(results) == 1
        assert results[0]["speaker"] == "unknown"


def test_speaker_discourse_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_speakers().filter(g.speaker.name == "unknown")
        q = q.columns(
            g.speaker.name.column_name("speaker"),
            g.speaker.discourses.name.column_name("discourses"),
            g.speaker.discourses.channel.column_name("channels"),
        )
        print(q.cypher())
        results = q.all()
        assert len(results) == 1
        assert results[0]["speaker"] == "unknown"
        assert results[0]["discourses"] == ["acoustic_corpus"]
        assert results[0]["channels"] == [0]
