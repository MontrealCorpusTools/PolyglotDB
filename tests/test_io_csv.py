import os

import pytest

from polyglotdb import CorpusContext


def test_to_csv(acoustic_utt_config, export_test_dir):
    export_path = os.path.join(export_test_dir, "results_export.csv")
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == "aa")
        q = q.columns(
            g.phone.label.column_name("label"),
            g.phone.duration.column_name("duration"),
            g.phone.begin.column_name("begin"),
        )
        q = q.order_by(g.phone.begin.column_name("begin"))
        q.to_csv(export_path)

    # ignore ids
    expected = [
        ["label", "duration", "begin"],
        ["aa", 0.0783100000000001, 2.70424],
        ["aa", 0.12199999999999989, 9.32077],
        ["aa", 0.03981000000000279, 24.56029],
    ]
    with open(export_path, "r") as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            if line == "":
                continue
            line = line.split(",")
            print(line)
            if i != 0:
                line = [line[0], float(line[1]), float(line[2])]
                assert line[0] == expected[i][0]
                assert line[1:] == pytest.approx(expected[i][1:], 1e-3)
            else:
                assert line == expected[i]
            i += 1

    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == "aa")
        q = q.columns(g.phone.label, g.phone.duration, g.phone.begin)
        q = q.order_by(g.phone.begin)
        q.to_csv(export_path)

    # ignore ids
    expected = [
        ["node_phone_label", "node_phone_duration", "node_phone_begin"],
        ["aa", 0.0783100000000001, 2.70424],
        ["aa", 0.12199999999999989, 9.32077],
        ["aa", 0.03981000000000279, 24.56029],
    ]
    with open(export_path, "r") as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            print(line)
            if line == "":
                continue
            line = line.split(",")
            print(line)
            if i != 0:
                line = [line[0], float(line[1]), float(line[2])]
                assert line[0] == expected[i][0]
                assert line[1:] == pytest.approx(expected[i][1:], 1e-3)
            else:
                assert line == expected[i]
            i += 1


@pytest.mark.acoustic
def test_csv_vot(acoustic_utt_config, vot_classifier_path, export_test_dir):
    pytest.skip()
    export_path = os.path.join(export_test_dir, "results_export_vot.csv")
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.reset_vot()
        stops = ["p", "t", "k"]  # , 'b', 'd', 'g']
        g.encode_class(stops, "stops")
        g.analyze_vot(
            stop_label="stops",
            classifier=vot_classifier_path,
            vot_min=15,
            vot_max=250,
            window_min=-30,
            window_max=30,
        )
        q = (
            g.query_graph(g.phone)
            .filter(g.phone.label.in_(stops))
            .columns(g.phone.vot.begin, g.phone.vot.end)
            .order_by(g.phone.begin)
        )
        q.to_csv(export_path)
        p_true = [
            (1.593, 1.649),
            (1.832, 1.848),
            (1.909, 1.98),
            (2.116, 2.137),
            (2.687, 2.703),
            (2.829, 2.8440000000000003),
            (2.934, 2.9490000000000003),
            (3.351, 3.403),
            (5.574, 5.593999999999999),
            (6.207, 6.2219999999999995),
            (6.736, 6.755999999999999),
            (7.02, 7.0489999999999995),
            (9.255, 9.287),
            (9.498, 9.514999999999999),
            (11.424, 11.479999999999999),
            (13.144, 13.206),
            (13.498, 13.523),
            (25.125, 25.14),
        ]
    p_csv = []
    with open(export_path, "r") as f:
        f.readline()
        for line in f:
            line = line.strip()
            if line == "":
                continue
            line = line.split(",")
            p_csv.append((float(line[0]), float(line[1])))
    for t, r in zip(p_true, p_csv):
        assert r == t
