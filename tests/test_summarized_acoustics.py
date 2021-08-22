import pytest
from polyglotdb import CorpusContext



@pytest.mark.acoustic
def test_phone_mean_pitch(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.pitch_source = 'praat'
        g.config.praat_path = praat_path
        g.config.pitch_algorithm = 'basic'
        g.analyze_pitch()
        results = g.get_acoustic_statistic('pitch', 'mean', by_phone=True)
        print(results)


@pytest.mark.acoustic
def test_speaker_mean_pitch(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        g.config.praat_path = praat_path
        g.config.pitch_algorithm = 'basic'
        results = g.get_acoustic_statistic('pitch', 'mean', by_phone=False, by_speaker=True)
        print(results)


@pytest.mark.acoustic
def test_phone_speaker_mean_pitch(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        g.config.praat_path = praat_path
        g.config.pitch_algorithm = 'basic'
        results = g.get_acoustic_statistic('pitch', 'mean', by_phone=True, by_speaker=True)
        print(results)
