import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)


@acoustic
def test_analyze_vot(acoustic_utt_config, autovot_path, vot_classifier_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.autovot_path = autovot_path
        stops = ['p', 't', 'k', 'b', 'd', 'g']
        g.encode_class(stops, 'stops')
        g.analyze_vot(stop_label="stops")
        #TODO: Go over all stops, not just /p/
        q = g.query_graph(g.phone).filter(g.phone.label.in_(stops)).columns(g.phone.label, g.phone.begin, g.phone.end, g.phone.id, g.phone.vot.begin, g.phone.vot.end).order_by(g.phone.begin)
        print(q.all())
        p_returns = [q.all()[i] for i in range(3)]
        #p_true = [(2.067, 2.144), (2.934, 2.959), (6.182, 6.234)]
        #for t, r in zip(p_true, p_returns):
        #    assert (r["node_vot_begin"][0], r["node_vot_end"][0]) == t

