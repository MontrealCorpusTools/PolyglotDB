import pytest

from polyglotdb import CorpusContext


def test_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_lexicon(g.lexicon_phone).filter(g.lexicon_phone.label.in_(["aa", "ih"]))
        q = q.order_by(g.lexicon_phone.label)
        q = q.columns(g.lexicon_phone.label.column_name("phone"))
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[0]["phone"] == "aa"
        assert results[1]["phone"] == "ih"


def test_filter_on_type_subset(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_lexicon(g.lexicon_phone).filter(g.lexicon_phone.label == "aa")
        q.create_subset("+syllabic")
        phone = g.phone.filter_by_subset("+syllabic")
        q = g.query_graph(phone)
        q = q.order_by(phone.begin.column_name("begin"))
        q = q.columns(
            phone.begin.column_name("begin"),
            phone.end.column_name("end"),
            phone.duration.column_name("duration"),
        )
        print(q.cypher())
        results = q.all()
        assert len(results) == 3
        assert abs(results[0]["begin"] - 2.704) < 0.001
        assert abs(results[0]["duration"] - 0.078) < 0.001

        assert abs(results[1]["begin"] - 9.320) < 0.001
        assert abs(results[1]["duration"] - 0.122) < 0.001

        assert abs(results[2]["begin"] - 24.560) < 0.001
        assert abs(results[2]["duration"] - 0.039) < 0.001


def test_path_on_type_subset(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        syllabics = ["aa", "ih"]
        q = g.query_lexicon(g.lexicon_phone).filter(g.lexicon_phone.label.in_(syllabics))
        q.create_subset("syllabic")

        print("begin aa.k number of syllabics in word")
        q = g.query_graph(g.phone).filter(g.phone.label == "aa")
        q = q.filter(g.phone.following.label == "k")

        q = q.columns(
            g.phone.word.phone.filter_by_subset("syllabic").count.column_name(
                "num_syllables_in_word"
            )
        )
        q = q.order_by(g.phone.word.begin)
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[0]["num_syllables_in_word"] == 2


def test_multiple_path_on_type_subset(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        syllabics = ["aa", "ih"]
        q = g.query_lexicon(g.lexicon_phone).filter(g.lexicon_phone.label.in_(syllabics))
        q.create_subset("syllabic")
        print("begin aa.k number of syllabics/segments in word")
        q = g.query_graph(g.phone).filter(g.phone.label == "aa")
        q = q.filter(g.phone.following.label == "k")

        q = q.columns(
            g.phone.word.phone.filter_by_subset("syllabic").count.column_name(
                "num_syllables_in_word"
            ),
            g.phone.word.phone.count.column_name("num_segments_in_word"),
        )
        q = q.order_by(g.phone.word.begin)
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[0]["num_segments_in_word"] == 5
        assert results[0]["num_syllables_in_word"] == 2


def test_filter_following_on_type_subset(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_lexicon(g.lexicon_phone).filter(g.lexicon_phone.label == "aa")
        q.create_subset("+syllabic")
        q = g.query_graph(g.phone).filter(g.phone.label == "t")
        q = q.filter(g.phone.following.subset == "+syllabic")
        print(g.phone.following.subset)
        q = q.columns(g.phone.following.label.column_name("following"))
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[0]["following"] == "aa"


def test_cache_subset_count(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        syllabics = ["aa", "ih"]
        q = g.query_lexicon(g.lexicon_phone).filter(g.lexicon_phone.label.in_(syllabics))
        q.create_subset("syllabic")
        q = g.query_graph(g.word)
        q.cache(g.word.phone.filter_by_subset("syllabic").count.column_name("num_syllables"))
        print(q.cypher())

        q = g.query_graph(g.phone).filter(g.phone.label == "aa")
        q = q.filter(g.phone.following.label == "k")

        q = q.columns(
            g.phone.word.num_syllables.column_name("num_syllables_in_word"),
            g.phone.word.phone.count.column_name("num_segments_in_word"),
        )
        q = q.order_by(g.phone.word.begin)
        print(q.cypher())
        results = q.all()
        assert len(results) == 2
        assert results[0]["num_segments_in_word"] == 5
        assert results[0]["num_syllables_in_word"] == 2
