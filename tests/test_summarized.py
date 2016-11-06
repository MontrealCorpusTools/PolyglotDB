
import pytest
from polyglotdb import CorpusContext
from polyglotdb.io import inspect_buckeye
from polyglotdb.exceptions import GraphQueryError


def test_get_measure(summarized_config):
    with CorpusContext(summarized_config) as g:
        res = g.get_measure('duration','mean','phone')
        print(res)
        assert(len(res)==33)
        for i, r in enumerate(res):
            if r[0] == 'uw':
                break
        assert(abs(res[i][1]-0.08043999999999973) < .0000000000001)

def test_phone_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone mean:")
        res = g.get_measure('duration','mean','phone')
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
        res = g.get_measure('duration','mean','phone', False, 'unknown')
        print(res)
        assert(len(res)==33)
        for i, r in enumerate(res):
            if r[0] == 'uw':
                break
        assert(abs(res[i][1]-0.08043999999999973) < .0000000000001)


def test_phone_mean_duration_speaker_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as g:
        res = g.get_measure('duration','mean','phone')
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
        # res =g.phone_mean_duration_with_speaker()
        res = g.get_measure('duration','mean','phone', True)
        print(res)
        assert(len(res)==33)
        for i, r in enumerate(res):
            if r[1] == 'uw':
                break
        assert(abs(res[i][2]-0.08043999999999973) < .0000000000001)

def test_phone_std_dev(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone std dev:")
        res = g.get_measure('duration','stdev','phone')
        print(res)
        for i, r in enumerate(res):
            if r[0] == 'uw':
                break

        assert(len(res)==33)
        assert(abs(res[i][1]-0.026573072836990105) < .0000000000001)



def test_phone_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone median:")
        res = g.get_measure('duration','median','phone')
        print(res)
        for i, r in enumerate(res):
            if r[0] == 'n':
                break
        assert(abs(res[i][1]-0.059820000000000206) < .0000000000001)


def test_word_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("mean duration (word):")
        res = g.get_measure('duration','mean','word')
        print(res)
        assert(len(res)==44)
        for i, r in enumerate(res):
            if r[0] == 'words':
                break
        assert(abs(res[i][1]-0.5340040000000001) < .0000000000001)

def test_word_mean_duration_with_speaker(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word mean:")
        res = g.get_measure('duration','mean','word', True)
        print(res)
        assert(len(res)==44)
        for i, r in enumerate(res):
            if r[1] == 'words':
                break
        assert(abs(res[i][2]-0.5340040000000001) < .0000000000001)
@pytest.mark.xfail
def test_word_mean_duration_with_speaker_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as g:
        g.encode_utterances()
        res = g.get_measure('duration','mean','word', True)
        print(res)
        for i, r in enumerate(res):
            if r[1] == 'that\'s':
                break
        assert(len(res)==9)
        assert(abs(res[i][2]-0.17431200000000002) < .0000000000001)

def test_word_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word median:")
        res = g.get_measure('duration','median','word')
        print(res)
        assert(len(res) == 44)
        for i, r in enumerate(res):
            if r[0] == 'words':
                break
        assert(abs(res[i][1]-0.5489699999999971) < .0000000000001)

def test_word_std_dev(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word std dev:")
        res = g.get_measure('duration','stdev','word')
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
        res = g.get_measure('duration','mean','syllable')
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
        res = g.get_measure('duration','mean','syllable', True)
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
        res = g.get_measure('duration','median','syllable')

        print(res)
        assert(len(res) == 55)

def test_syllable_std_dev(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("syllable std dev:")
        res = g.get_measure('duration','stdev','syllable')
        assert(len(res) == 55)


@pytest.mark.xfail
def test_baseline_buckeye_word(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        res = g.get_measure('duration','baseline','word')
        print(res)
        assert(len(res) == 9)

        assert(abs(res['they']-0.11224799999999968)< .0000000000001)

def test_baseline_word(summarized_config):
    with CorpusContext(summarized_config) as g:
        res = g.get_measure('duration','baseline','word')
        print(res)
        
        assert(abs(res['this']-0.20937191666666685)< .0000000000001)
        assert(len(res)==44)

def test_baseline_speaker_word(summarized_config):
    with CorpusContext(summarized_config) as g:
        res = g.get_measure('duration','baseline','word', False, 'unknown')
        print(res)
        assert(abs(res['this']-0.20937191666666685)< .0000000000001)
        assert(len(res)==44)


@pytest.mark.xfail
def test_baseline_speaker_buckeye_word(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        res = g.get_measure('duration','baseline','word', False, 'tes')
        print(res)
        assert(len(res) == 9)
        assert(abs(res['they']-0.11224799999999968)< .0000000000001)

def test_baseline_utterance(acoustic_config):

    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil'])
        g.encode_utterances(min_pause_length = 0.15)
        res = g.get_measure('duration','baseline','utterance')
        print(res)

def test_baseline_syllable(acoustic_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    with CorpusContext(acoustic_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()
        res = g.get_measure('duration','baseline','syllable')
        print(res)




@pytest.mark.xfail
def test_average_speech_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_utterances()
        res = g.average_speech_rate()
        print(res)
        assert(abs(res[0][1] - 2.6194399113581532) < 0.001)
        assert(len(res)==1)

@pytest.mark.xfail
def test_average_speech_rate_buckeye(graph_db, buckeye_test_dir):
    with CorpusContext('directory_buckeye', **graph_db) as c:
        c.reset()
        parser = inspect_buckeye(buckeye_test_dir)
        c.load(parser, buckeye_test_dir)
        with pytest.raises(GraphQueryError):
            res = c.average_speech_rate()
        c.encode_pauses('^[{<].*$')
        c.encode_utterances(min_pause_length=0)
        with pytest.raises(GraphQueryError):
            res = c.average_speech_rate()
        c.encode_syllabic_segments(['eh','ae','ah','er','ey','ao'])
        c.encode_syllables('maxonset')
        res = c.average_speech_rate()
        print(res)
        assert(abs(res[0][1]-5.929060725) < .00001)
        assert(len(res)==1)
