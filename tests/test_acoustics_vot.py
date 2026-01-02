import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext


@pytest.mark.acoustic
def test_analyze_vot(acoustic_utt_config, vot_classifier_path):
    pytest.skip()
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
            .columns(
                g.phone.label,
                g.phone.begin,
                g.phone.end,
                g.phone.id,
                g.phone.vot.begin,
                g.phone.vot.end,
            )
            .order_by(g.phone.begin)
        )
        p_returns = q.all()
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

        for t, r in zip(p_true, p_returns):
            assert (r["node_vot_begin"][0], r["node_vot_end"][0]) == t
