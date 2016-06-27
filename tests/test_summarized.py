
import pytest

from polyglotdb import CorpusContext


def test_phone_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone mean:")
        print(g.phone_mean_duration('ah'))

def test_phone_std_dev(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone std dev:")
        print(g.phone_std_dev('ah'))

def test_all_phone_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("all phone median:")
        print(g.all_phone_median())

def test_phone_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("phone median:")
        print(g.phone_median('ah'))

def test_get_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("get mean duration (word):")
        print(g.get_mean_duration('word'))

def test_word_mean_duration(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("mean duration (word):")
        print(g.word_mean_duration('words'))

def test_word_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word median:")
        print(g.word_median('words'))

def test_all_word_median(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("all word median:")
        print(g.all_word_median())

def test_word_std_dev(summarized_config):
    with CorpusContext(summarized_config) as g:
        print("word std dev:")
        print(g.word_std_dev('words'))

def test_syllable_mean_duration(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
    

    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("all syllable mean:")
        print(g.syllable_mean_duration('ah.s'))

def test_syllable_median(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
   

    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("syllable median:")
        print(g.syllable_median('w.er.d.z')) 

def test_all_syllable_median(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
   

    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("all syllable median:")
        print(g.all_syllable_median())

def test_syllable_std_dev(summarized_config):
    syllabics = ['ae','aa','uw','ay','eh', 'ih', 'aw', 'ey', 'iy',
                'uh','ah','ao','er','ow']
   

    with CorpusContext(summarized_config) as g:
        g.encode_syllabic_segments(syllabics)
        g.encode_syllables()

        print("syllable std dev:")
        print(g.syllable_std_dev('w.er.d.z'))
