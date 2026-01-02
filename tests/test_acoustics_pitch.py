import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext


@pytest.mark.acoustic
def test_analyze_discourse_pitch(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.praat_path = praat_path

        r = g.query_graph(g.utterance).all()
        assert len(r)
        for u in r:
            track = g.analyze_utterance_pitch(u, pitch_source="praat", min_pitch=80, max_pitch=100)
            if u.begin < 24:
                assert len(track)


@pytest.mark.acoustic
def test_save_new_pitch_track(acoustic_utt_config_praat_pitch, praat_path):
    with CorpusContext(acoustic_utt_config_praat_pitch) as g:
        g.config.praat_path = praat_path
        r = g.query_graph(g.utterance).all()
        assert len(r)
        for u in r:
            print(u.id)
            track = g.analyze_utterance_pitch(u, pitch_source="praat")
            print(len(track))
            for x in track:
                x["F0"] = 100
                print(x)
            print("UPDATING TRACK")

            g.update_utterance_pitch_track(u, track)

        q = g.query_graph(g.utterance).columns(g.utterance.id, g.utterance.pitch.track)
        for r in q.all():
            print(r)
            print(len(r.track))
            for point in r.track:
                print(point.time, point["F0"])
                assert point["F0"] == 100


@pytest.mark.acoustic
def test_analyze_pitch_basic_praat(acoustic_utt_config_praat_pitch):
    with CorpusContext(acoustic_utt_config_praat_pitch) as g:
        assert g.discourse_has_acoustics("pitch", g.discourses[0])
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.pitch.track)
        print(q.cypher())
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert len(r.track)


@pytest.mark.acoustic
def test_reset_utterances(acoustic_utt_config_praat_pitch):
    with CorpusContext(acoustic_utt_config_praat_pitch) as g:
        assert g.discourse_has_acoustics("pitch", g.discourses[0])
        g.reset_utterances()
        g.encode_utterances(0.15)
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.pitch.track)
        print(q.cypher())
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert len(r.track)


@pytest.mark.acoustic
def test_track_mean_query(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch()
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(
            g.phone.begin.column_name("begin"),
            g.phone.end,
            g.phone.pitch.track,
            g.phone.pitch.mean,
        )
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert r.track
            assert r["Mean_F0"]
            print(r.track, r["Mean_F0"])
            calc_mean = sum(x["F0"] for x in r.track) / len(r.track)
            assert abs(r["Mean_F0"] - calc_mean) < 0.001


@pytest.mark.acoustic
def test_track_following_mean_query(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch()
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(
            g.phone.begin.column_name("begin"),
            g.phone.end,
            g.phone.pitch.track,
            g.phone.following.pitch.mean.column_name("following_phone_pitch_mean"),
        )
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert r.track
            assert r["following_phone_pitch_mean"]
            print(r.track, r["following_phone_pitch_mean"])
            calc_mean = sum(x["F0"] for x in r.track) / len(r.track)
            assert abs(r["following_phone_pitch_mean"] - calc_mean) > 0.001


@pytest.mark.acoustic
def test_track_hierarchical_mean_query(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch()
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(
            g.phone.begin.column_name("begin"),
            g.phone.end,
            g.phone.pitch.track,
            g.phone.word.pitch.mean.column_name("word_pitch_mean"),
        )
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert r.track
            assert r["word_pitch_mean"]
            print(r.track, r["word_pitch_mean"])
            calc_mean = sum(x["F0"] for x in r.track) / len(r.track)
            assert abs(r["word_pitch_mean"] - calc_mean) > 0.001


@pytest.mark.acoustic
def test_track_hierarchical_following_mean_query(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch()
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(
            g.phone.begin.column_name("begin"),
            g.phone.end,
            g.phone.pitch.track,
            g.phone.word.pitch.mean.column_name("word_pitch_mean"),
            g.phone.word.following.pitch.mean.column_name("following_word_pitch_mean"),
        )
        results = q.all()
        assert len(results) > 0
        for r in results:
            print(r["begin"])
            assert len(r.track)
            assert r["word_pitch_mean"]
            print(r["word_pitch_mean"], r["following_word_pitch_mean"])
            assert r["word_pitch_mean"] != r["following_word_pitch_mean"]


@pytest.mark.acoustic
def test_track_hierarchical_utterance_mean_query(
    acoustic_utt_config, results_test_dir, praat_path
):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch()
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(
            g.phone.label,
            g.phone.pitch.track,
            g.phone.syllable.following.pitch.mean.column_name("following_syllable_pitch_mean"),
            g.phone.syllable.following.following.pitch.mean.column_name(
                "following_following_syllable_pitch_mean"
            ),
            g.phone.utterance.pitch.mean.column_name("utterance_pitch_mean"),
            g.phone.utterance.pitch.min.column_name("utterance_pitch_min"),
            g.phone.utterance.pitch.max.column_name("utterance_pitch_max"),
        )
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert len(r.track)
            assert r["utterance_pitch_mean"]
            assert r["utterance_pitch_min"]
            assert r["utterance_pitch_max"]
            print(r["utterance_pitch_mean"], r["following_syllable_pitch_mean"])
            with pytest.raises(KeyError):
                assert r["utterance_pitch_mean"] != r["following_word_pitch_mean"]
            assert r["utterance_pitch_mean"] != r["following_syllable_pitch_mean"]
            assert (
                r["following_following_syllable_pitch_mean"] != r["following_syllable_pitch_mean"]
            )
        q.to_csv(
            os.path.join(results_test_dir, "test_track_hierarchical_utterance_mean_query.txt")
        )


@pytest.mark.acoustic
def test_analyze_pitch_basic_reaper(acoustic_utt_config, reaper_path):
    if not os.path.exists(reaper_path):
        pytest.skip("no reaper available")
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.reaper_path = reaper_path
        g.analyze_pitch(source="reaper", multiprocessing=False)


@pytest.mark.acoustic
def test_analyze_pitch_gendered_praat(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch(source="praat", algorithm="gendered")


@pytest.mark.acoustic
def test_analyze_pitch_speaker_adjusted_praat(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch(source="praat", algorithm="speaker_adjusted")
        assert g.discourse_has_acoustics("pitch", "acoustic_corpus")

        g.reset_acoustic_measure("pitch")
        assert not g.discourse_has_acoustics("pitch", g.discourses[0])


def test_query_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]

        g.reset_acoustics()
        expected_pitch = {
            Decimal("4.23"): {"F0": 98},
            Decimal("4.24"): {"F0": 100},
            Decimal("4.25"): {"F0": 99},
            Decimal("4.26"): {"F0": 95.8},
            Decimal("4.27"): {"F0": 95.8},
        }
        properties = [("F0", float)]
        if "pitch" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "pitch", properties)
            g.encode_hierarchy()
        g.save_acoustic_track("pitch", "acoustic_corpus", expected_pitch, utterance_id=utt_id)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.label, g.phone.pitch.track)
        print(q.cypher())
        results = q.all()
        assert len(results[0].track) == len(expected_pitch.items())
        print(sorted(expected_pitch.items()))
        print(results[0].track)
        for point in results[0].track:
            assert round(point["F0"], 1) == expected_pitch[point.time]["F0"]


def test_query_aggregate_pitch(acoustic_utt_config_basic_pitch):
    with CorpusContext(acoustic_utt_config_basic_pitch) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.label, g.phone.pitch.min, g.phone.pitch.max, g.phone.pitch.mean)
        print(q.cypher())
        results = q.all()

        assert results[0]["Min_F0"] == 95.8
        assert results[0]["Max_F0"] == 100
        assert round(results[0]["Mean_F0"], 2) == 97.72


def test_relativize_pitch(acoustic_utt_config_basic_pitch):
    with CorpusContext(acoustic_utt_config_basic_pitch) as g:
        mean_f0 = 97.72
        sd_f0 = 1.88997
        expected_pitch = {
            Decimal("4.23"): {"F0": 98, "F0_relativized": (98 - mean_f0) / sd_f0},
            Decimal("4.24"): {"F0": 100, "F0_relativized": (100 - mean_f0) / sd_f0},
            Decimal("4.25"): {"F0": 99, "F0_relativized": (99 - mean_f0) / sd_f0},
            Decimal("4.26"): {"F0": 95.8, "F0_relativized": (95.8 - mean_f0) / sd_f0},
            Decimal("4.27"): {"F0": 95.8, "F0_relativized": (95.8 - mean_f0) / sd_f0},
        }
        g.relativize_acoustic_measure("pitch", by_speaker=True)
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.pitch
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == len(expected_pitch.items())
        print(sorted(expected_pitch.items()))
        print(results[0].track)
        for point in results[0].track:
            print(point)
            assert round(point["F0_relativized"], 5) == round(
                expected_pitch[point.time]["F0_relativized"], 5
            )

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.pitch
        ac.relative = True
        q = q.columns(g.phone.label, ac.min, ac.max, ac.mean)
        results = q.all()
        assert results[0]["Min_F0"] == 95.8
        assert results[0]["Max_F0"] == 100
        assert results[0]["Mean_F0"] == mean_f0
        min_rel = (95.8 - mean_f0) / sd_f0
        max_rel = (100 - mean_f0) / sd_f0
        assert abs(results[0]["Min_F0_relativized"] - min_rel) < 0.01
        assert abs(results[0]["Max_F0_relativized"] - max_rel) < 0.01
        assert results[0]["Mean_F0_relativized"] - 0 < 0.01

        g.reset_relativized_acoustic_measure("pitch")
        assert g.hierarchy.acoustic_properties["pitch"] == {("F0", float)}

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.pitch
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == 5
        for r in results:
            for p in r.track:
                assert not p.has_value("F0_relativized")


def test_export_pitch(acoustic_utt_config_basic_pitch):
    with CorpusContext(acoustic_utt_config_basic_pitch) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.label.column_name("label"), g.phone.pitch.track)
        print(q.cypher())
        results = q.all()

        t = results.rows_for_csv()
        assert next(t) == {"label": "ow", "time": Decimal("4.23"), "F0": 98}
        assert next(t) == {"label": "ow", "time": Decimal("4.24"), "F0": 100}
        assert next(t) == {"label": "ow", "time": Decimal("4.25"), "F0": 99}
        assert next(t) == {"label": "ow", "time": Decimal("4.26"), "F0": 95.8}
        assert next(t) == {"label": "ow", "time": Decimal("4.27"), "F0": 95.8}
