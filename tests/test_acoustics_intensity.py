import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext


def test_query_intensity(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]

        expected_intensity = {
            Decimal("4.23"): {"Intensity": 98},
            Decimal("4.24"): {"Intensity": 100},
            Decimal("4.25"): {"Intensity": 99},
            Decimal("4.26"): {"Intensity": 95.8},
            Decimal("4.27"): {"Intensity": 95.8},
        }
        properties = [("Intensity", float)]

        if "intensity" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "intensity", properties)
            g.encode_hierarchy()
        g.save_acoustic_track(
            "intensity", "acoustic_corpus", expected_intensity, utterance_id=utt_id
        )

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.label, g.phone.intensity.track)
        print(q.cypher())
        results = q.all()

        print(sorted(expected_intensity.items()))
        print(results[0].track)
        for point in results[0].track:
            assert round(point["Intensity"], 1) == expected_intensity[point.time]["Intensity"]


def test_relativize_intensity(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]

        expected_intensity = {
            Decimal("4.23"): {"Intensity": 98},
            Decimal("4.24"): {"Intensity": 100},
            Decimal("4.25"): {"Intensity": 99},
            Decimal("4.26"): {"Intensity": 95.8},
            Decimal("4.27"): {"Intensity": 95.8},
        }
        properties = [("Intensity", float)]

        if "intensity" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "intensity", properties)
            g.encode_hierarchy()
        g.save_acoustic_track(
            "intensity", "acoustic_corpus", expected_intensity, utterance_id=utt_id
        )

        mean_intensity = 97.72
        sd_intensity = 1.88997
        expected_intensity = {
            Decimal("4.23"): {
                "Intensity": 98,
                "Intensity_relativized": (98 - mean_intensity) / sd_intensity,
            },
            Decimal("4.24"): {
                "Intensity": 100,
                "Intensity_relativized": (100 - mean_intensity) / sd_intensity,
            },
            Decimal("4.25"): {
                "Intensity": 99,
                "Intensity_relativized": (99 - mean_intensity) / sd_intensity,
            },
            Decimal("4.26"): {
                "Intensity": 95.8,
                "Intensity_relativized": (95.8 - mean_intensity) / sd_intensity,
            },
            Decimal("4.27"): {
                "Intensity": 95.8,
                "Intensity_relativized": (95.8 - mean_intensity) / sd_intensity,
            },
        }
        g.relativize_acoustic_measure("intensity", by_speaker=True)
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.intensity
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == len(expected_intensity.items())
        print(sorted(expected_intensity.items()))
        print(results[0].track)
        for point in results[0].track:
            print(point)
            assert round(point["Intensity_relativized"], 5) == round(
                expected_intensity[point.time]["Intensity_relativized"], 5
            )

        g.reset_relativized_acoustic_measure("intensity")
        assert g.hierarchy.acoustic_properties["intensity"] == {("Intensity", float)}

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        ac = g.phone.intensity
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == 5
        for r in results:
            for p in r.track:
                assert not p.has_value("Intensity_relativized")


@pytest.mark.acoustic
def test_analyze_intensity_basic_praat(
    acoustic_utt_config, praat_path, results_test_dir, acoustic_syllabics
):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.praat_path = praat_path
        g.analyze_intensity()
        assert g.discourse_has_acoustics("intensity", g.discourses[0])
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.intensity.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, "intensity_data.csv")
        q.to_csv(output_path)
        assert len(results) > 0
        for r in results:
            assert len(r.track)
        q = g.query_graph(g.phone).filter(
            g.phone.label.not_in_(acoustic_syllabics),
            g.phone.previous.subset == "syllabic",
            g.phone.following.subset == "syllabic",
            g.phone.begin == g.phone.syllable.begin,
        )
        q_onset = q.columns(
            g.phone.id.column_name("traj_id"),
            g.phone.label.column_name("onset"),
            g.phone.intensity.track.column_name("intensity"),
        )
        results = q_onset.all()
        assert len(results) > 0
        q_onset.to_csv(os.path.join(results_test_dir, "intensity_data_onset.csv"))
        q = g.query_graph(g.phone).filter(
            g.phone.label.not_in_(acoustic_syllabics),
            g.phone.previous.subset == "syllabic",
            g.phone.following.subset == "syllabic",
            g.phone.begin == g.phone.syllable.begin,
        )
        q_prev = q.columns(
            g.phone.id.column_name("traj_id"),
            g.phone.label.column_name("onset"),
            g.phone.previous.label.column_name("previous"),
            g.phone.previous.begin.column_name("previous_begin"),
            g.phone.previous.end.column_name("previous_end"),
            g.phone.previous.intensity.track.column_name("intensity_prev"),
        )
        results = q_prev.all()
        assert len(results) > 0
        q_prev.to_csv(os.path.join(results_test_dir, "intensity_data_prev.csv"))
        q = g.query_graph(g.phone).filter(
            g.phone.label.not_in_(acoustic_syllabics),
            g.phone.previous.subset == "syllabic",
            g.phone.following.subset == "syllabic",
            g.phone.begin == g.phone.syllable.begin,
        )
        # to get the intensity track of the following vowel
        q_foll = q.columns(
            g.phone.id.column_name("traj_id"),
            g.phone.label.column_name("onset"),
            g.phone.following.label.column_name("following"),
            g.phone.following.begin.column_name("following_begin"),
            g.phone.following.end.column_name("following_end"),
            g.phone.following.intensity.track.column_name("intensity_foll"),
        )
        q_foll.to_csv(os.path.join(results_test_dir, "intensity_data_foll.csv"))
        results = q_foll.all()
        assert len(results) > 0

        g.reset_acoustic_measure("intensity")
        assert not g.discourse_has_acoustics("intensity", g.discourses[0])
