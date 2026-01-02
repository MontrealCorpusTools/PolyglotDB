import os

import pytest

from polyglotdb import CorpusContext


def test_subset_enrichment(acoustic_config):
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
    phone_class = ["ae", "aa", "d", "r"]
    with CorpusContext(acoustic_config) as c:
        c.reset_class("syllabic")
        c.reset_class("test")
        c.encode_class(syllabics, "syllabic")
        c.encode_class(phone_class, "test")
        assert len(c.hierarchy.subset_types["phone"]) == 2


def test_stress_enrichment(stressed_config):
    syllabics = "AA0,AA1,AA2,AH0,AH1,AH2,AE0,AE1,AE2,AY0,AY1,AY2,ER0,ER1,ER2,EH0,EH1,EH2,EY1,EY2,IH0,IH1,IH2,IY0,IY1,IY2,UW0,UW1,UW2".split(
        ","
    )
    with CorpusContext(stressed_config) as c:
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables("maxonset")
        c.encode_stress_to_syllables(regex="[0-2]$")

        assert c.hierarchy.has_type_property("syllable", "stress")


def test_stress_enrichment_no_clean(stressed_config):
    syllabics = "AA0,AA1,AA2,AH0,AH1,AH2,AE0,AE1,AE2,AY0,AY1,AY2,ER0,ER1,ER2,EH0,EH1,EH2,EY1,EY2,IH0,IH1,IH2,IY0,IY1,IY2,UW0,UW1,UW2".split(
        ","
    )
    with CorpusContext(stressed_config) as c:
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables("maxonset")
        c.encode_stress_to_syllables(clean_phone_label=False)

        assert c.hierarchy.has_type_property("syllable", "stress")

        q = c.query_graph(c.syllable)
        q = q.filter(c.syllable.word.label == "began")

        q = q.columns(
            c.syllable.label.column_name("syllable"),
            c.syllable.stress.column_name("syllable_stress"),
            c.syllable.word.label.column_name("word"),
            c.syllable.word.begin.column_name("word_begin"),
            c.syllable.word.end.column_name("word_end"),
            c.syllable.discourse.name.column_name("file"),
        )
        q = q.limit(10)
        res = q.all()
        for r in res:
            assert r["syllable_stress"] is not None


def test_relativized_enrichment_syllables(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        # c.encode_measure("word_median")

        # assert(c.hierarchy.has_type_property("word","median_duration"))
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
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables()
        c.encode_baseline("syllable", "duration")

        assert c.hierarchy.has_token_property("syllable", "baseline_duration")


def test_relativized_enrichment_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        c.encode_pauses(["sil", "um"])
        c.encode_utterances(min_pause_length=0)

        c.encode_baseline("utterance", "duration")

        assert c.hierarchy.has_token_property("utterance", "baseline_duration")


@pytest.mark.skip
def dicthelper(dict1, dict2):
    # compare innermost dictionaries
    current1, current2 = dict1, dict2
    while True:
        if type(current1[list(current1.keys())[0]]) == dict:
            current1 = current1[list(current1.keys())[0]]
        else:
            break
    while True:
        if type(current2[list(current2.keys())[0]]) == dict:
            current2 = current2[list(current2.keys())[0]]
        else:
            break

    for key in current1.keys():
        if abs(current1[key] - current2[key]) > 0.00000001:
            return False
    return True


def test_speaker_enrichment(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        expected = {
            "th": 0.04493500000000017,
            "<SIL>": 0.6284645454545452,
            "y": 0.05754000000000037,
            "b": 0.06809999999999894,
            "er": 0.1971710000000002,
            "uw": 0.08043999999999973,
            "ow": 0.18595500000000018,
            "p": 0.051516666666666655,
            "z": 0.08597333333333353,
            "jh": 0.04727999999999977,
            "l": 0.1076199999999997,
            "sh": 0.09417000000000186,
            "w": 0.07460249999999968,
            "n": 0.0737177777777775,
            "ch": 0.05305000000000071,
            "ih": 0.06382066666666676,
            "eh": 0.05799199999999978,
            "r": 0.09273624999999973,
            "ng": 0.05112571428571457,
            "ae": 0.19313571428571402,
            "s": 0.10893125000000002,
            "ah": 0.1770525000000001,
            "aa": 0.08004000000000093,
            "t": 0.0645437499999999,
            "iy": 0.1256781818181817,
            "g": 0.04078499999999963,
            "ay": 0.14554000000000014,
            "d": 0.09151333333333334,
            "m": 0.13204625000000064,
            "hh": 0.05832999999999977,
            "f": 0.0654300000000001,
            "k": 0.09175999999999981,
            "dh": 0.036620000000000055,
        }

        c.encode_measure("duration", "mean", "phone", False)

        # need a better way to test this
        query = c.query_graph(c.phone).columns(
            c.phone.label.column_name("label"), c.phone.mean_duration.column_name("mean_duration")
        )
        for r in query.all():
            assert abs(r["mean_duration"] - expected[r["label"]]) < 0.001


def test_timed_token_enrichment(acoustic_config, timed_csv_enrich_file):
    with CorpusContext(acoustic_config) as c:
        c.enrich_tokens_with_csv(
            timed_csv_enrich_file,
            "word",
            discourse_id_column="discourse",
            timestamp_column="time",
        )
        q = c.query_graph(c.word)
        q = q.filter(c.word.label == "slow")
        results = q.all()

        assert results[0]["prop2"] == 2
        assert results[0]["prop1"] == 1.0
        assert results[0]["prop3"] == True  # noqa


def test_track_import(acoustic_config, track_import_file):
    with CorpusContext(acoustic_config) as c:
        c.save_track_from_csv("formant_external", track_import_file, ["f1", "f2"])

        assert c.discourse_has_acoustics("formant_external", "acoustic_corpus")
        q = c.query_graph(c.phone)
        q = q.columns(
            c.phone.label, c.phone.begin, c.phone.end, c.phone.formant_external.track
        ).filter(c.phone.begin <= 3, c.phone.end >= 3)
        q = q.order_by(c.phone.begin)
        results = q.all()
        first_time, first_values = next(results[0].track.items())
        assert first_values.get("f1") == 100
