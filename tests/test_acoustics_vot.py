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
        p_returns = [q.all()[i] for i in range(28)]
        p_true = [(1.473, 1.478), (1.829, 1.8339999999999999), (1.88, 1.8849999999999998), (2.041, 2.046), (2.631, 2.6359999999999997), (2.774, 2.779), (2.906, 2.911), (3.352, 3.3569999999999998), (4.179, 4.184), (4.565, 4.57), (5.501, 5.507000000000001), (6.228, 6.234999999999999), (6.732, 6.737), (6.736, 6.741), (7.02, 7.029999999999999), (9.187, 9.196), (9.413, 9.418000000000001), (11.424, 11.429), (13.144, 13.194), (13.496, 13.501000000000001), (16.862, 16.869999999999997), (19.282, 19.292), (20.823, 20.828), (21.379, 21.384), (21.674, 21.679), (22.197, 22.201999999999998), (24.506, 24.511)]
        for t, r in zip(p_true, p_returns):
            assert (r["node_vot_begin"][0], r["node_vot_end"][0]) == t

