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
        g.analyze_vot()
