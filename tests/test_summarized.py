
import pytest
from polyglotdb.graph.func import Count
from polyglotdb import CorpusContext
from polyglotdb.io import inspect_buckeye

def test_phone_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone mean:")
        res = g.phone_mean_duration()
        print(res)
        assert(len(res)==33)
        for i, r in enumerate(res):
            if r[0] == 'uw':
                break
        assert(abs(res[i][1]-0.08043999999999973) < .0000000000001)

def test_phone_mean_duration_speaker(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone mean:")
        g.encode_utterances()
        res = g.phone_mean_duration('unknown')
        print(res)
        assert(len(res)==33)
        for i, r in enumerate(res):
            if r[0] == 'uw':
                break
        assert(abs(res[i][1]-0.08043999999999973) < .0000000000001)


def test_phone_mean_duration_speaker_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as g:
        res = g.phone_mean_duration()
        print(res)
        assert(len(res)==16)
        dx,eh= 0,0
        for i,r in enumerate(res):
            if r[0] == 'dx':
                dx = i
            if r[0] == 'eh':
                eh = i
        assert(abs(res[dx][1]-0.029999999999999805) < .0000000000001)
        assert(abs(res[eh][1]-0.04932650000000005) < .0000000000001)




def test_phone_mean_duration_with_speaker(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone mean by speaker:")
        g.encode_utterances()
        res =g.phone_mean_duration_with_speaker()
        print(res)
        assert(len(res)==33)
        for i, r in enumerate(res):
            if r[1] == 'uw':
                break
        assert(abs(res[i][2]-0.08043999999999973) < .0000000000001)

def test_phone_std_dev(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone std dev:")
        res = g.phone_std_dev()
        print(res)
        for i, r in enumerate(res):
            if r[0] == 'uw':
                break

        assert(len(res)==33)
        assert(abs(res[i][1]-0.026573072836990105) < .0000000000001)

def test_all_phone_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("all phone median:")
        res = g.all_phone_median()


        print(res)
        assert(abs(res-0.07682000000000011) < .0000000000001)
        assert(type(res) == float)

def test_phone_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone median:")
        res = g.phone_median()
        print(res)
        for i, r in enumerate(res):
            if r[0] == 'n':
                break
        assert(abs(res[i][1]-0.059820000000000206) < .0000000000001)


def test_get_mean_duration(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']


    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("get mean duration (syl):")
        toget = 'phone'
        res = g.get_mean_duration(toget)
        print(res)

        assert(type(res) == float)
        if toget == 'phone':
            assert(abs(res-0.13164172413793104) < .0000000000001 )

def test_word_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("mean duration (word):")
        res = g.word_mean_duration()
        print(res)
        assert(len(res)==44)
        for i, r in enumerate(res):
            if r[0] == 'words':
                break
        assert(abs(res[i][1]-0.5340040000000001) < .0000000000001)




def test_word_mean_duration_with_speaker(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word mean:")
        res = g.word_mean_duration_with_speaker()
        print(res)
        assert(len(res)==44)
        for i, r in enumerate(res):
            if r[1] == 'words':
                break
        assert(abs(res[i][2]-0.5340040000000001) < .0000000000001)

def test_word_mean_duration_with_speaker_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as g:
        g.encode_utterances()
        res=g.word_mean_duration_with_speaker()
        print(res)
        for i, r in enumerate(res):
            if r[1] == 'that\'s':
                break
        assert(len(res)==9)
        assert(abs(res[i][2]-0.17431200000000002) < .0000000000001)

def test_word_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word median:")
        res = g.word_median()
        print(res)
        assert(len(res) == 44)
        for i, r in enumerate(res):
            if r[0] == 'words':
                break
        assert(abs(res[i][1]-0.5489699999999971) < .0000000000001)

def test_all_word_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("all word median:")
        res = g.all_word_median()
        print(res)
        assert(type(res) == float)
        assert(abs(res-0.2736300000000007) < .0000000000001)


def test_word_std_dev(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word std dev:")
        res = g.word_std_dev()
        print(res)

        assert(len(res)==44)
        for i, r in enumerate(res):
            if r[0] == 'words':
                break
        assert(abs(res[i][1]-0.26996736762060747) < .0000000000001)

def test_syllable_mean_duration(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("syllable mean:")
        res =g.syllable_mean_duration()
        print(res)
        assert(len(res) == 55)
        for i, r in enumerate(res):
            if r[0] == 'w.er.d.z':
                break
        assert(abs(res[i][1]-0.5340040000000001) < .0000000000001)

def test_syllable_mean_duration_with_speaker_buckeye(graph_db, buckeye_test_dir):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext('directory_buckeye', **graph_db) as g:
        g.reset()
        parser = inspect_buckeye(buckeye_test_dir)
        g.load(parser, buckeye_test_dir)
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()
        res = g.syllable_mean_duration_with_speaker()
        print(res)
        assert(len(res) == 11)
        for i, r in enumerate(res):
            if r[1] == 'dh.ae.s':
                break
        assert(abs(res[i][2]-0.17030199999999995) < .0000000000001)


def test_syllable_median(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("syllable median:")
        res = g.syllable_median()
        print(res)
        assert(len(res) == 55)

def test_all_syllable_median(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("all syllable median:")
        res = g.all_syllable_median()
        print(res)
        assert(type(res) == float)

def test_syllable_std_dev(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("syllable std dev:")
        res = g.syllable_std_dev()
        assert(len(res) == 55)

@pytest.mark.xfail
def test_baseline_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        res = c.baseline_duration()
        print(res)
        assert(len(res) == 9)

        assert(abs(res['they']-0.11224799999999968)< .0000000000001)

def test_baseline(summarized_config):
    with CorpusContext(summarized_config) as g:
        res = g.baseline_duration()
        print(res)
        assert(abs(res['this']-0.20937191666666685)< .0000000000001)
        assert(len(res)==44)

def test_baseline_speaker(summarized_config):
    with CorpusContext(summarized_config) as g:
        res = g.baseline_duration('unknown')
        print(res)
        assert(abs(res['this']-0.20937191666666685)< .0000000000001)
        assert(len(res)==44)

@pytest.mark.xfail
def test_baseline_speaker_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        res = c.baseline_duration('tes')
        print(res)
        assert(len(res) == 9)

        assert(abs(res['they']-0.11224799999999968)< .0000000000001)

@pytest.mark.xfail
def test_average_speech_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_utterances()
        res = g.average_speech_rate()
        print(res)
        assert(abs(res[0][1] - 2.6194399113581532) < 0.001)
        assert(len(res)==1)

def test_average_speech_rate_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        c.reset()
        parser = inspect_buckeye(buckeye_test_dir)
        c.load(parser, buckeye_test_dir)
        c.encode_utterances()
        res = c.average_speech_rate()
        print(res)
        assert(abs(res[0][1]-2.4439013552543876) < .0000000000001)
        assert(len(res)==1)
