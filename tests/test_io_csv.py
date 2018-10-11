import pytest
import os

from polyglotdb.io import inspect_csv

from polyglotdb.io.types.content import (OrthographyAnnotationType,
                                         TranscriptionAnnotationType,
                                         NumericAnnotationType)

from polyglotdb.io.helper import guess_type

from polyglotdb.exceptions import DelimiterError
from polyglotdb import CorpusContext

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)

def test_to_csv(acoustic_utt_config, export_test_dir):
    export_path = os.path.join(export_test_dir, 'results_export.csv')
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.label.column_name('label'),
                      g.phone.duration.column_name('duration'),
                      g.phone.begin.column_name('begin'))
        q = q.order_by(g.phone.begin.column_name('begin'))
        q.to_csv(export_path)

    # ignore ids
    expected = [['label', 'duration', 'begin'],
                ['aa', 0.0783100000000001, 2.70424],
                ['aa', 0.12199999999999989, 9.32077],
                ['aa', 0.03981000000000279, 24.56029]]
    with open(export_path, 'r') as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            if line == '':
                continue
            line = line.split(',')
            if i != 0:
                line = [line[0], float(line[1]), float(line[2])]
            print(line)
            assert line[0] == expected[i][0]
            assert line[1:] == pytest.approx(expected[i][1:], 1e-3)
            i += 1

    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.label,
                      g.phone.duration,
                      g.phone.begin)
        q = q.order_by(g.phone.begin)
        q.to_csv(export_path)

    # ignore ids
    expected = [['node_phone_label', 'node_phone_duration', 'node_phone_begin'],
                ['aa', 0.0783100000000001,2.70424],
                ['aa', 0.12199999999999989, 9.32077],
                ['aa', 0.03981000000000279, 24.56029]]
    with open(export_path, 'r') as f:
        i = 0
        for line in f.readlines():
            line = line.strip()
            print(line)
            if line == '':
                continue
            line = line.split(',')
            if i != 0:
                line = [line[0], float(line[1]), float(line[2])]
            print(line)
            assert line[0] == expected[i][0]
            assert line[1:] == pytest.approx(expected[i][1:], 1e-3)
            i += 1

@acoustic
def test_csv_vot(acoustic_utt_config, autovot_path, vot_classifier_path, export_test_dir):
    export_path = os.path.join(export_test_dir, 'results_export_vot.csv')
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.autovot_path = autovot_path
        stops = ['p', 't', 'k', 'b', 'd', 'g']
        g.encode_class(stops, 'stops')
        g.analyze_vot(stop_label="stops")
        #TODO: Go over all stops, not just /p/
        q = g.query_graph(g.phone).filter(g.phone.label.in_(stops)).columns(g.phone.vot.begin, g.phone.vot.end).order_by(g.phone.begin)
        q.to_csv(export_path)
    p_true = [(1.473, 1.478), (1.829, 1.8339999999999999), (1.88, 1.8849999999999998), (2.041, 2.046), (2.631, 2.6359999999999997), (2.774, 2.779), (2.906, 2.911), (3.352, 3.3569999999999998), (4.179, 4.184), (4.565, 4.57), (5.501, 5.507000000000001), (6.228, 6.234999999999999), (6.732, 6.737), (6.736, 6.741), (7.02, 7.029999999999999), (9.187, 9.196), (9.413, 9.418000000000001), (11.424, 11.429), (13.144, 13.194), (13.496, 13.501000000000001), (16.862, 16.869999999999997), (19.282, 19.292), (20.823, 20.828), (21.379, 21.384), (21.674, 21.679), (22.197, 22.201999999999998), (24.506, 24.511)]
    p_csv = []
    with open(export_path, 'r') as f:
        f.readline()
        for line in f:
            line = line.strip()
            if line == '':
                continue
            line = line.split(',')
            #For some odd reason the values are being written to CSV as 1.23/1.23 for any given value of the vot,
            #definitely should be fixed but i have no clue where this is from
            p_csv.append((float(line[0].split('/')[0]), float(line[1].split('/')[0])))
    for t, r in zip(p_true, p_csv):
        assert r == t

