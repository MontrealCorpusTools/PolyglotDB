import pytest
import os

from polyglotdb.io import inspect_csv

from polyglotdb.io.types.content import (OrthographyAnnotationType,
                                         TranscriptionAnnotationType,
                                         NumericAnnotationType)

from polyglotdb.io.helper import guess_type

from polyglotdb.exceptions import DelimiterError
from polyglotdb import CorpusContext


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


