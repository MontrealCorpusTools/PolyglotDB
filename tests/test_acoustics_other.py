import os

import pytest

from polyglotdb import CorpusContext

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)


# def test_run_script(acoustic_utt_config, praat_path, praatscript_test_dir):
#     with CorpusContext(acoustic_utt_config) as g:
#         g.config.praat_path = praat_path
#         script_path = os.path.join(praatscript_test_dir, 'COG.praat')
#         sibilantfile_path = os.path.join(textgrid_test_dir, 'acoustic_corpus_sib1.wav')
#         output = run_script(g.config.praat_path, script_path, sibilantfile_path, 0.0, 0.137, '1', '2')
#         output = output.strip()
#         assert (float(output) == 4654.12)
#         assert (output.replace('.','').isnumeric())
#
# def test_analyze_script_file(acoustic_utt_config, praat_path, praatscript_test_dir):
#     with CorpusContext(acoustic_utt_config) as g:
#         g.config.praat_path = praat_path
#         script_path = os.path.join(praatscript_test_dir, 'COG.praat')
#         sibilantfile_path = os.path.join(textgrid_test_dir, 'acoustic_corpus_sib1.wav')
#         output = g.analyze_script_file(script_path, sibilantfile_path, 0.0, 0.137, None, '1', '2')
#         assert(output == 4654.12)

@acoustic
def test_analyze_script(acoustic_utt_config, praat_path, praatscript_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.praat_path = praat_path
        g.encode_class(['s', 'z', 'sh', 'zh'], 'sibilant')
        script_path = os.path.join(praatscript_test_dir, 'sibilant_jane.praat')
        g.analyze_script('sibilant', script_path, stop_check=None, call_back=None)
        q = g.query_graph(g.phone).filter(g.phone.subset == 'sibilant')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.peak)
        results = q.all()
        assert (len(results) > 0)
        for r in results:
            assert (r.values)
        q2 = g.query_graph(g.phone).filter(g.phone.subset == 'sibilant')
        q2 = q2.columns(g.phone.begin, g.phone.end, g.phone.spread)
        results = q2.all()
        assert (len(results) > 0)
        for r in results:
            assert (r.values)
