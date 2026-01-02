import os

import pytest

from polyglotdb import CorpusContext

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


@pytest.mark.acoustic
def test_analyze_script(acoustic_utt_config, praat_path, praatscript_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.praat_path = praat_path
        g.encode_class(["s", "z", "sh", "zh"], "sibilant")
        script_path = os.path.join(praatscript_test_dir, "sibilant_jane.praat")
        props = g.analyze_script(
            subset="sibilant",
            annotation_type="phone",
            script_path=script_path,
            stop_check=None,
            call_back=None,
            multiprocessing=False,
        )
        assert props == sorted(["cog", "peak", "slope", "spread"])
        q = g.query_graph(g.phone).filter(g.phone.subset == "sibilant")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.peak)
        results = q.all()
        assert len(results) > 0
        for r in results:
            assert r.values
        q2 = g.query_graph(g.phone).filter(g.phone.subset == "sibilant")
        q2 = q2.columns(g.phone.begin, g.phone.end, g.phone.spread)
        results = q2.all()
        assert len(results) > 0
        for r in results:
            assert r.values


@pytest.mark.acoustic
def test_analyze_track_script(acoustic_utt_config, praat_path, praatscript_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.encode_class(["ih", "iy", "ah", "uw", "er", "ay", "aa", "ae", "eh", "ow"], "vowel")
        script_path = os.path.join(praatscript_test_dir, "formants.praat")
        props = [("F1", float), ("F2", float), ("F3", float)]
        arguments = [0.01, 0.025, 5, 5500]
        g.analyze_track_script(
            "formants_other",
            props,
            script_path,
            annotation_type="phone",
            subset="vowel",
            file_type="vowel",
            arguments=arguments,
        )

        assert "formants_other" in g.hierarchy.acoustics

        assert g.discourse_has_acoustics("formants_other", g.discourses[0])
        q = g.query_graph(g.phone).filter(g.phone.label == "ow")
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants_other.track)
        results = q.all()

        assert len(results) > 0
        print(len(results))
        for r in results:
            # print(r.track)
            assert len(r.track)

        g.reset_acoustic_measure("formants_other")
        assert not g.discourse_has_acoustics("formants_other", g.discourses[0])
