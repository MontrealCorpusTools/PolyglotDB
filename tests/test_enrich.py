
import pytest
import os

from polyglotdb import CorpusContext

from polyglotdb.io.enrichment import (enrich_lexicon_from_csv, enrich_features_from_csv,
                                    enrich_discourses_from_csv, enrich_speakers_from_csv)
"""
def test_lexicon_enrichment(timed_config, csv_test_dir):
    path = os.path.join(csv_test_dir, 'timed_enrichment.txt')
    with CorpusContext(timed_config) as c:
        enrich_lexicon_from_csv(c, path)

        q = c.query_graph(c.word).filter(c.word.neighborhood_density < 10)

        q = q.columns(c.word.label.column_name('label'))

        res = q.all()

        assert(all(x['label'] == 'guess' for x in res))

        q = c.query_graph(c.word).filter(c.word.label == 'i')

        res = q.all()

        assert(res[0]['frequency'] == 150)
        assert(res[0]['part_of_speech'] == 'PRP')
        assert(res[0]['neighborhood_density'] == 17)

        q = c.query_graph(c.word).filter(c.word.label == 'cute')

        res = q.all()

        assert(res[0]['frequency'] is None)
        assert(res[0]['part_of_speech'] == 'JJ')
        assert(res[0]['neighborhood_density'] == 14)

        levels = c.lexicon.get_property_levels('part_of_speech')
        assert(set(levels) == set(['NN','VB','JJ','IN','PRP']))

def test_feature_enrichment(timed_config, csv_test_dir):
    path = os.path.join(csv_test_dir, 'timed_features.txt')
    with CorpusContext(timed_config) as c:
        enrich_features_from_csv(c, path)

        q = c.query_graph(c.phone).filter(c.phone.vowel_height == 'lowhigh')

        q = q.columns(c.phone.label.column_name('label'))

        res = q.all()

        assert(all(x['label'] == 'ay' for x in res))

        q = c.query_graph(c.phone).filter(c.phone.place_of_articulation == 'velar')

        q = q.columns(c.phone.label.column_name('label'))

        res = q.all()

        assert(all(x['label'] in ['k','g'] for x in res))

def test_speaker_enrichment_csv(fave_corpus_config, csv_test_dir):
    path = os.path.join(csv_test_dir, 'fave_speaker_info.txt')
    with CorpusContext(fave_corpus_config) as c:
        enrich_speakers_from_csv(c, path)

        q = c.query_graph(c.phone).filter(c.phone.speaker.is_interviewer == True)

        q = q.columns(c.phone.label.column_name('label'),
                    c.phone.speaker.name.column_name('speaker'))

        res = q.all()

        assert(all(x['speaker'] == 'Interviewer' for x in res))

def test_discourse_enrichment(fave_corpus_config, csv_test_dir):
    path = os.path.join(csv_test_dir, 'fave_discourse_info.txt')
    with CorpusContext(fave_corpus_config) as c:
        enrich_discourses_from_csv(c, path)

        q = c.query_graph(c.phone).filter(c.phone.discourse.noise_level == 'high')

        q = q.columns(c.phone.label.column_name('label'),
                    c.phone.discourse.name.column_name('discourse'))

        res = q.all()

        assert(all(x['discourse'] == 'fave_test' for x in res))

def test_subset_enrichment(acoustic_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    phone_class = ['ae', 'aa', 'd', 'r']
    with CorpusContext(acoustic_config) as c:
        c.reset_class('syllabic')
        c.reset_class('test')
        c.encode_class(syllabics, "syllabic")
        c.encode_class(phone_class, "test")
        assert(len(c.hierarchy.subset_types['phone'])==2)

def test_stress_enrichment(stressed_config):
    syllabics= "AA0,AA1,AA2,AH0,AH1,AH2,AE0,AE1,AE2,AY0,AY1,AY2,ER0,ER1,ER2,EH0,EH1,EH2,EY1,EY2,IH0,IH1,IH2,IY0,IY1,IY2,UW0,UW1,UW2".split(",")
    with CorpusContext(stressed_config) as c:
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables("maxonset")
        c.encode_stresstone_to_syllables('stress','[0-2]$')

        assert(c.hierarchy.has_type_property("syllable","stress"))

def test_relativized_enrichment_syllables(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        # c.encode_measure("word_median")

        # assert(c.hierarchy.has_type_property("word","median_duration"))
        syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
        c.encode_syllabic_segments(syllabics)
        c.encode_syllables()
        c.encode_measure("baseline_duration_syllable")

        assert(c.hierarchy.has_type_property("syllable","baseline_duration"))

def test_relativized_enrichment_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        c.encode_pauses(['sil', 'um'])
        c.encode_utterances(min_pause_length = 0)

        c.encode_measure('baseline_duration_utterance')


"""
def test_speaker_annotation(acoustic_config):
    data = {'unknown' : {'average_duration' : {'uw' : 0.08043999}}}

    with CorpusContext(acoustic_config) as c:
        c.enrich_speaker_annotations(data)



def test_baseline_speaker_word(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        res = g.baseline_duration("word",'unknown')
        print(res)
        assert(abs(res['this']-0.20937191666666685)< .0000000000001)
        assert(len(res)==44)


