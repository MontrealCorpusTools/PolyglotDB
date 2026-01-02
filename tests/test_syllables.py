from polyglotdb import CorpusContext
from polyglotdb.syllabification.main import syllabify
from polyglotdb.syllabification.maxonset import split_nonsyllabic_maxonset, split_ons_coda_maxonset
from polyglotdb.syllabification.probabilistic import (
    norm_count_dict,
    split_nonsyllabic_prob,
    split_ons_coda_prob,
)


def test_find_onsets(timed_config):
    syllabics = ["ae", "aa", "uw", "ay", "eh"]
    expected_onsets = {("k",), (), ("d",), ("t",), ("g",)}
    expected_freqs = {("k",): 2, (): 3, ("d",): 1, ("t",): 1, ("g",): 1}
    with CorpusContext(timed_config) as c:
        c.encode_syllabic_segments(syllabics)
        assert c.has_syllabics
        onsets = c.find_onsets()
        assert set(onsets.keys()) == expected_onsets
        assert onsets == expected_freqs


def test_find_codas(timed_config):
    expected_codas = {("t", "s"), ("r",), ("t",), ("g", "z"), (), ("s",)}
    expected_freqs = {
        ("t", "s"): 1,
        (): 2,
        ("r",): 2,
        ("t",): 1,
        ("g", "z"): 1,
        ("s",): 1,
    }
    with CorpusContext(timed_config) as c:
        codas = c.find_codas()
        assert set(codas.keys()) == expected_codas
        assert codas == expected_freqs


def test_probabilistic_syllabification(acoustic_config, timed_config, acoustic_syllabics):
    with CorpusContext(timed_config) as c:
        onsets = norm_count_dict(c.find_onsets())
        codas = norm_count_dict(c.find_codas())
    print(onsets)
    print(codas)
    expected = [(["z", "g"], 1), (["g", "z"], 2), (["t", "s", "k"], 2), (["t", "d"], 1)]
    for s, e in expected:
        result = split_ons_coda_prob(s, onsets, codas)
        print(s, e, result)
        assert e == result

    with CorpusContext(acoustic_config) as c:
        c.reset_class("syllabic")
        c.encode_syllabic_segments(acoustic_syllabics)
        assert c.has_syllabics
        onsets = norm_count_dict(c.find_onsets())
        codas = norm_count_dict(c.find_codas())
    # nonsyllabic
    expected = [(["d", "g", "z"], 2), (["sh"], 0)]
    for s, e in expected:
        result = split_nonsyllabic_prob(s, onsets, codas)
        print(s, e, result)
        assert e == result


def test_maxonset_syllabification(timed_config):
    with CorpusContext(timed_config) as c:
        onsets = set(c.find_onsets().keys())

    print(onsets)
    expected = [(["z", "g"], 1), (["g", "z"], 2), (["t", "s", "k"], 2), (["t", "d"], 1)]
    for s, e in expected:
        result = split_ons_coda_maxonset(s, onsets)
        print(s, e, result)
        assert e == result

    # nonsyllabic
    expected = [(["d", "g", "z"], 1), (["sh"], 0)]
    for s, e in expected:
        result = split_nonsyllabic_maxonset(s, onsets)
        print(s, e, result)
        assert e == result


def test_maxonset_syllabification_custom(syllabification_config):
    with CorpusContext(syllabification_config) as c:
        onsets = {("S", "T", "R"), ("N",)}
        syllabics = ["EH1", "AH0", "AE1", "AO2"]
        c.encode_type_subset("phone", syllabics, "syllabic")
        c.encode_syllables(custom_onsets=onsets)
        syllables = ["EH1.K", "S.T.R.AH0", "AE1", "N.AO2.T"]
        assert set(c.syllables) == set(syllables)


def test_syllabify():
    expected = {
        ("n", "ay", "iy", "v"): [{"label": "n.ay"}, {"label": "iy.v"}],
        ("l", "ow", "w", "er"): [{"label": "l.ow"}, {"label": "w.er"}],
    }
    s = ["ay", "iy", "ow", "er"]
    o = [("n",), ("v",), ("w",), ("l",)]
    c = [("v",)]
    for k, v in expected.items():
        test = syllabify(k, s, o, c, "maxonset")
        assert len(test) == len(v)
        for i, x in enumerate(v):
            for k2, v2 in x.items():
                assert v2 == test[i][k2]


def test_encode_syllables_acoustic(acoustic_config):
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
    with CorpusContext(acoustic_config) as c:
        c.encode_syllabic_segments(syllabics)
        assert c.has_syllabics
        c.encode_syllables()
        assert c.has_syllables

        q = c.query_graph(c.phone).filter(c.phone.label == "dh")
        q = q.filter(c.phone.begin == c.phone.syllable.begin)
        q = q.order_by(c.phone.begin)
        q = q.columns(c.phone.label, c.phone.begin)

        results = q.all()
        assert len(results) == 5

        q = c.query_graph(c.syllable)
        q = q.columns(
            c.syllable.phone.filter_by_subset("onset").label.column_name("onset"),
            c.syllable.phone.filter_by_subset("nucleus").label.column_name("nucleus"),
            c.syllable.phone.filter_by_subset("coda").label.column_name("coda"),
        )
        for r in q.all():
            assert all(x not in syllabics for x in r["onset"])
            assert all(x in syllabics for x in r["nucleus"])
            assert all(x not in syllabics for x in r["coda"])


def test_encode_stress_from_word_property(acoustic_utt_config, stress_pattern_file):
    with CorpusContext(acoustic_utt_config) as c:
        c.enrich_lexicon_from_csv(stress_pattern_file)
        c.encode_stress_from_word_property("stress_pattern")
        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.stress == "1")
        q = q.columns(
            c.syllable.label.column_name("syllable"),
            c.syllable.word.label.column_name("word"),
        )
        results = q.all()
        print(q.all())
        assert len(results) == 8
        for r in q.all():
            assert r["word"] in ["words", "acoustic", "intensity", "corpus"]
            if r["word"] == "words":
                assert r["syllable"] == "w.er.d.z"
            elif r["word"] == "acoustic":
                assert r["syllable"] == "k.uw"
            elif r["word"] == "intensity":
                assert r["syllable"] == "t.eh.n"
            elif r["word"] == "corpus":
                assert r["syllable"] == "k.er.p"
