import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext
from polyglotdb.acoustics.formants.base import analyze_formant_points
from polyglotdb.acoustics.formants.refined import (
    analyze_formant_points_refinement,
    get_mean_SD,
    save_formant_point_data,
)


@pytest.mark.acoustic
def test_analyze_formants_basic_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_formant_tracks(multiprocessing=False)
        assert g.discourse_has_acoustics("formants", g.discourses[0])
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, "formant_data.csv")
        q.to_csv(output_path)
        assert len(results) > 0
        for r in results:
            assert len(r.track)


def test_analyze_formants_vowel_segments(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.encode_class(["ih", "iy", "ah", "uw", "er", "ay", "aa", "ae", "eh", "ow"], "vowel")
        g.analyze_formant_tracks(vowel_label="vowel", multiprocessing=False)
        assert g.discourse_has_acoustics("formants", g.discourses[0])
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, "formant_vowel_data.csv")
        q.to_csv(output_path)
        assert len(results) > 0
        print(len(results))
        for r in results:
            # print(r.track)
            assert len(r.track)

        g.reset_acoustic_measure("formants")
        assert not g.discourse_has_acoustics("formants", g.discourses[0])


@pytest.mark.acoustic
def test_analyze_formants_gendered_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.hierarchy.add_speaker_properties(g, [("gender", str)])
        assert g.hierarchy.has_speaker_property("gender")
        g.config.praat_path = praat_path
        g.analyze_formant_tracks()
        assert g.discourse_has_acoustics("formants", g.discourses[0])
        assert "formants" in g.hierarchy.acoustics
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, "formant_data.csv")
        q.to_csv(output_path)
        assert len(results) > 0
        for r in results:
            assert len(r.track)


def test_query_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]
        g.reset_acoustics()
        expected_formants = {
            Decimal("4.23"): {"F1": 501, "F2": 1500, "F3": 2500},
            Decimal("4.24"): {"F1": 502, "F2": 1499, "F3": 2498},
            Decimal("4.25"): {"F1": 503, "F2": 1498, "F3": 2500},
            Decimal("4.26"): {"F1": 504, "F2": 1497, "F3": 2502},
            Decimal("4.27"): {"F1": 505, "F2": 1496, "F3": 2500},
        }
        properties = [("F1", float), ("F2", float), ("F3", float)]
        if "formants" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "formants", properties)
            g.encode_hierarchy()
        g.save_acoustic_track(
            "formants", "acoustic_corpus", expected_formants, utterance_id=utt_id
        )

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.label, g.phone.formants.track)
        print(q.cypher())
        results = q.all()

        print(sorted(expected_formants.items()))
        print(results[0])
        print(repr(results[0]))
        print(repr(results))
        print(results)
        print(results[0].track)
        for point in results[0].track:
            assert round(point["F1"], 1) == expected_formants[point.time]["F1"]
            assert round(point["F2"], 1) == expected_formants[point.time]["F2"]
            assert round(point["F3"], 1) == expected_formants[point.time]["F3"]


def test_relative_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]
        expected_formants = {
            Decimal("4.23"): {"F1": 501, "F2": 1500, "F3": 2500},
            Decimal("4.24"): {"F1": 502, "F2": 1499, "F3": 2498},
            Decimal("4.25"): {"F1": 503, "F2": 1498, "F3": 2500},
            Decimal("4.26"): {"F1": 504, "F2": 1497, "F3": 2502},
            Decimal("4.27"): {"F1": 505, "F2": 1496, "F3": 2500},
        }
        properties = [("F1", float), ("F2", float), ("F3", float)]
        if "formants" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "formants", properties)
            g.encode_hierarchy()
        g.save_acoustic_track(
            "formants", "acoustic_corpus", expected_formants, utterance_id=utt_id
        )
        means = {"F1": 503, "F2": 1498, "F3": 2500}
        sds = {"F1": 1.5811, "F2": 1.5811, "F3": 1.4142}

        for k, v in expected_formants.items():
            for f in ["F1", "F2", "F3"]:
                expected_formants[k]["{}_relativized".format(f)] = (v[f] - means[f]) / sds[f]

        g.relativize_acoustic_measure("formants", by_speaker=True)
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.formants
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == len(expected_formants.items())
        print(sorted(expected_formants.items()))
        print(results[0].track)
        for point in results[0].track:
            print(point)
            for f in ["F1", "F2", "F3"]:
                rel_name = "{}_relativized".format(f)
                assert round(point[rel_name], 4) == round(
                    expected_formants[point.time][rel_name], 4
                )

        g.reset_relativized_acoustic_measure("formants")

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.formants
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == 5
        for r in results:
            for p in r.track:
                for f in ["F1", "F2", "F3"]:
                    rel_name = "{}_relativized".format(f)
                    assert not p.has_value(rel_name)


def test_query_aggregate_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]
        g.reset_acoustics()
        expected_formants = {
            Decimal("4.23"): {"F1": 501, "F2": 1500, "F3": 2500},
            Decimal("4.24"): {"F1": 502, "F2": 1499, "F3": 2498},
            Decimal("4.25"): {"F1": 503, "F2": 1498, "F3": 2500},
            Decimal("4.26"): {"F1": 504, "F2": 1497, "F3": 2502},
            Decimal("4.27"): {"F1": 505, "F2": 1496, "F3": 2500},
        }
        properties = [("F1", float), ("F2", float), ("F3", float)]
        if "formants" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "formants", properties)
            g.encode_hierarchy()
        g.save_acoustic_track(
            "formants", "acoustic_corpus", expected_formants, utterance_id=utt_id
        )

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(
            g.phone.label,
            g.phone.formants.min,
            g.phone.formants.max,
            g.phone.formants.mean,
        )
        print(q.cypher())
        results = q.all()
        print(results[0])
        assert round(results[0]["Min_F1"], 0) > 0
        assert round(results[0]["Max_F1"], 0) > 0
        assert round(results[0]["Mean_F1"], 0) > 0

        assert round(results[0]["Min_F2"], 0) > 0
        assert round(results[0]["Max_F2"], 0) > 0
        assert round(results[0]["Mean_F2"], 0) > 0

        assert round(results[0]["Min_F3"], 0) > 0
        assert round(results[0]["Max_F3"], 0) > 0
        assert round(results[0]["Mean_F3"], 0) > 0


def test_formants(acoustic_utt_config, praat_path, export_test_dir):
    output_path = os.path.join(export_test_dir, "formant_vowel_data.csv")
    with CorpusContext(acoustic_utt_config) as g:
        test_phone_label = "ow"
        g.config.praat_path = praat_path
        g.encode_class(["ih", "iy", "ah", "uw", "er", "ay", "aa", "ae", "eh", "ow"], "vowel")
        g.analyze_formant_points(vowel_label="vowel")
        assert g.hierarchy.has_token_property("phone", "F1")
        q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
        q = q.columns(g.phone.begin, g.phone.end, g.phone.F1.column_name("F1"))
        q.to_csv(output_path)
        results = q.all()
        assert len(results) > 0

        for r in results:
            assert r["F1"]


def test_extract_formants_full(acoustic_utt_config, praat_path, export_test_dir):
    output_path = os.path.join(export_test_dir, "full_formant_vowel_data.csv")
    with CorpusContext(acoustic_utt_config) as g:
        test_phone_label = "ow"
        g.config.praat_path = praat_path
        g.encode_class(["ih", "iy", "ah", "uw", "er", "ay", "aa", "ae", "eh", "ow"], "vowel")
        print("starting test")
        _ = analyze_formant_points_refinement(g, "vowel")
        assert g.hierarchy.has_token_property("phone", "F1")
        q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
        q = q.columns(g.phone.begin, g.phone.end, g.phone.F1.column_name("F1"))
        q.to_csv(output_path)
        results = q.all()
        assert len(results) > 0

        for r in results:
            assert r["F1"]

        assert g.hierarchy.has_token_property("phone", "F1")
        g.reset_formant_points()
        assert not g.hierarchy.has_token_property("phone", "F1")
