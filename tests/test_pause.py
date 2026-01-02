from polyglotdb import CorpusContext


def test_encode_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.reset_pauses()
        g.encode_pauses(["sil"])
        q = g.query_graph(g.pause)
        print(q.cypher())
        assert len(q.all()) == 11
        assert g.has_pauses

        q = g.query_graph(g.word).filter(g.word.label.in_(["sil"]), g.word.subset != "pause")
        print(q.cypher())
        assert q.count() == 0

        g.reset_pauses()
        q = g.query_graph(g.pause)
        assert len(q.all()) == 0
        q = g.query_graph(g.word).filter(
            g.word.label.in_(["sil", "um", "uh"]), g.word.subset != "pause"
        )
        print(q.cypher())
        assert q.count() != 0
        assert not g.has_pauses

        g.encode_pauses(["sil", "um", "uh"])
        q = g.query_graph(g.pause)
        print(q.cypher())
        assert len(q.all()) == 14
        assert g.has_pauses

        q = g.query_graph(g.word).filter(
            g.word.label.in_(["sil", "um", "uh"]), g.word.subset != "pause"
        )
        assert q.count() == 0

        g.reset_pauses()
        q = g.query_graph(g.word).filter(
            g.word.label.in_(["sil", "um", "uh"]), g.word.subset != "pause"
        )
        assert q.count() != 0
        assert not g.has_pauses


def test_query_with_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(["sil", "uh", "um"])
        q = g.query_graph(g.word).filter(g.word.label == "cares")
        q = q.columns(
            g.word.following.label.column_name("following"),
            g.word.following_pause.label.column_name("following_pause"),
            g.word.following_pause.duration.column_name("following_pause_duration"),
        )
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        print(results)
        assert len(results) == 1
        assert results[0]["following"] == "this"
        assert results[0]["following_pause"] == ["sil", "um"]
        assert abs(results[0]["following_pause_duration"] - 1.035027) < 0.001

        q = g.query_graph(g.word).filter(g.word.label == "this")
        q = q.columns(
            g.word.previous.label.column_name("previous"),
            g.word.previous_pause.label.column_name("previous_pause"),
            g.word.previous_pause.begin,
            g.word.previous_pause.end,
            g.word.previous_pause.duration.column_name("previous_pause_duration"),
        )
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[1]["previous"] == "cares"
        assert results[1]["previous_pause"] == ["sil", "um"]
        assert abs(results[1]["previous_pause_duration"] - 1.035027) < 0.001

        g.encode_pauses(["sil"])
        q = g.query_graph(g.word).filter(g.word.label == "words")
        q = q.columns(
            g.word.following.label.column_name("following"),
            g.word.following_pause.label.column_name("following_pause"),
            g.word.following_pause.duration.column_name("following_pause_duration"),
        )
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert len(results) == 5
        assert results[0]["following"] == "and"
        assert results[0]["following_pause"] == ["sil"]
        assert abs(results[0]["following_pause_duration"] - 1.152438) < 0.001


def test_pause_both_sides(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(["sil", "uh", "um"])
        q = g.query_graph(g.word).filter(g.word.label == "cares")
        q = q.columns(
            g.word.following.label.column_name("following"),
            g.word.following_pause.label.column_name("following_pause"),
            g.word.following_pause.duration.column_name("following_pause_duration"),
            g.word.previous.label.column_name("previous"),
            g.word.previous_pause.label.column_name("previous_pause"),
            g.word.previous_pause.duration.column_name("previous_pause_duration"),
        )
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        print(results)
        assert len(results) == 1
        assert results[0]["following"] == "this"
        assert results[0]["following_pause"] == ["sil", "um"]
        assert abs(results[0]["following_pause_duration"] - 1.035027) < 0.001
        assert results[0]["previous"] == "who"
        assert results[0]["previous_pause"] is None
        assert results[0]["previous_pause_duration"] is None


def test_hierarchical_pause_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(["sil"])
        q = g.query_graph(g.phone).filter(g.phone.word.label == "words")
        q = q.filter(g.phone.label == "w")
        q = q.columns(
            g.phone.word.following.label.column_name("following"),
            g.phone.word.following_pause.label.column_name("following_pause"),
            g.phone.word.following_pause.duration.column_name("following_pause_duration"),
        )
        q = q.order_by(g.phone.word.begin)
        print(q.cypher())
        print(q.cypher_params())
        results = q.all()
        assert results[0]["following"] == "and"
        assert results[0]["following_pause"] == ["sil"]
        assert abs(results[0]["following_pause_duration"] - 1.152438) < 0.001

        syllabics = [
            "ae",
            "aa",
            "uw",
            "ay",
            "eh",
            "ih",
            "aw",
            "ey",
            "iy",
            "uh",
            "ah",
            "ao",
            "er",
            "ow",
        ]
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()
        print(g.syllable)
        q = g.query_graph(g.phone).filter(g.phone.word.label == "words")
        q = q.filter(g.phone.label == "w")
        q = q.columns(
            g.phone.word.following.label.column_name("following"),
            g.phone.word.following_pause.label.column_name("following_pause"),
            g.phone.word.following_pause.duration.column_name("following_pause_duration"),
        )
        q = q.order_by(g.phone.word.begin)
        print(q.cypher())
        print(q.cypher_params())
        results = q.all()
        assert len(results) == 5
        assert results[0]["following"] == "and"
        assert results[0]["following_pause"] == ["sil"]

        assert abs(results[0]["following_pause_duration"] - 1.152438) < 0.001

        g.reset_syllables()


def test_buckeye_pause(graph_db, buckeye_test_dir):
    import os

    from polyglotdb.io import inspect_buckeye

    with CorpusContext("discourse_buckeye", **graph_db) as c:
        c.reset()
        word_path = os.path.join(buckeye_test_dir, "test.words")
        parser = inspect_buckeye(word_path)
        c.load(parser, word_path)
        c.encode_pauses("^[<{].*$")
