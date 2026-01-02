import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext

# def test_query(acoustic_utt_config, praat_path):
#     with CorpusContext(acoustic_utt_config) as g:
#         g.config.praat_path = praat_path
#         q = g.query_graph(g.phone).filter(g.phone.label.in_(['s']))
#         sound_files = q.all()
#         #q.to_csv("C:\\Users\\samih\\Documents\\0_SPADE_labwork\\sib_query.csv")
#         num_sound_files = len(sound_files)
#         assert(num_sound_files)


def test_wav_info(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        sf = g.discourse_sound_file("acoustic_corpus")
        assert sf["sampling_rate"] == 16000
        assert sf["num_channels"] == 1
