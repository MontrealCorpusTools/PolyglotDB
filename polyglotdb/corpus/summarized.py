import math
from .base import BaseContext
from polyglotdb.graph.func import *
import re

class SummarizedContext(BaseContext):

    """
    Get the mean duration of each phone in corpus

    Parameters
    ----------
    speaker : str
        a speaker name, if desired (defaults to None)

    Returns
    -------
    result : list
        the average duration of each phone in the corpus
    """
    def phone_mean_duration(self, speaker = None):
        phone = getattr(self, self.phone_name)
        self.encode_utterances()
        if speaker is not None:
            q = self.query_graph(phone).filter(phone.speaker.name==speaker)
        else:
            q = self.query_graph(phone)

        q=q.group_by(phone.label.column_name('label'))
    
        result = q.aggregate(Average(phone.duration))
      
        return result
    
    """
    Gets average phone durations by speaker

    Returns
    -------
    result : list
        the average duration of each phone in the corpus, by speaker
    """

    def phone_mean_duration_with_speaker(self):
        phone = getattr(self, self.phone_name)
        self.encode_utterances()
        
        q = self.query_graph(phone)
        q=q.group_by(phone.speaker.name.column_name("speaker"), phone.label.column_name('label'))
        
        result = q.aggregate(Average(phone.duration))
        
        return result

    """
    Get the standard deviation of each phone in a corpus

    Returns
    -------
    result : list
        the standard deviation of each phone in the corpus
    """
    def phone_std_dev(self):
        phone = getattr(self, self.phone_name)
        result = self.query_graph(phone).group_by(phone.label.column_name('label')).aggregate(Stdev(phone.duration))#.filter(phone.label==to_find)

        return result

    """
    Get the median duration of all the phones in the corpus

    Returns
    -------
    float
        median duration of all the phones in the corpus
    """
    def all_phone_median(self):
        phone = getattr(self, self.phone_name)
        return self.query_graph(phone).aggregate(Median(phone.duration))


    """
    Get the median duration of each phone in a corpus

    Returns
    -------
    result : list
        the median duration of each phone in the corpus
    """
    def phone_median(self):
        phone = getattr(self, self.phone_name)
        return self.query_graph(phone).group_by(phone.label.column_name('label')).aggregate(Median(phone.duration))#.filter(phone.label == to_find)
      
    """
    Get the mean duration of all words or all phones in the corpus

    Parameters
    ----------
    type : str
        the type (word or phone)

    Returns
    -------
    result : float
        the average duration of all words or all phones
    """

    def get_mean_duration(self, type):
        result = 0.0
        if type == 'phone':
            phone = getattr(self, self.phone_name)
            q = self.query_graph(phone)
            result = q.aggregate(Average(phone.duration))
        elif type == 'word':
            word = getattr(self,self.word_name)
            q = self.query_graph(word)
            result = q.aggregate(Average(word.duration))
        elif type == 'syllable':
            syllable = self.syllable
            q = self.query_graph(syllable)
            result = q.aggregate(Average(syllable.duration))
        return result

    #words
    """
    Get the mean duration of each word

    Returns
    -------
    result : list
        the average duration of each word
    """
    def word_mean_duration(self):
        word = getattr(self,self.word_name)
        result = self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Average(word.duration))#.filter(word.label==to_find)
       
        return result


    """
    Gets average word durations by speaker

    Returns
    -------
    result : list
        the average duration of each word in the corpus, by speaker
    """

    def word_mean_duration_with_speaker(self):
        word = getattr(self, self.word_name)
        self.encode_utterances()
        
        q = self.query_graph(word)
      
        #    q = q.columns()
        q=q.group_by(word.speaker.name.column_name("speaker"), word.label.column_name('label'))
        
        result = q.aggregate(Average(word.duration))
        
        return result
    """
    Get the median duration of each word

    Returns
    -------
    list
        the median duration of each word
    """
    def word_median(self):
        word = getattr(self, self.word_name)
        return self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Median(word.duration))#.filter(word.label == to_find)
      
    """
    Get the median duration of all the words in the corpus

    Returns
    -------
    float
        median duration of all the words in the corpus
    """
    def all_word_median(self):
        word = getattr(self, self.word_name)
        return self.query_graph(word).aggregate(Median(word.duration))

    """
    Get the standard deviation of each word in a corpus

    Returns
    -------
    result : list
        the standard deviation of each word in the corpus
    """
    def word_std_dev(self):
        word = getattr(self, self.word_name)
        return self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Stdev(word.duration))#.filter(word.label==to_find)


    """
    Get the baseline duration of each word in corpus. 
    Baseline duration is determined by summing the average durations of constituent phones for a word. 
    If there is no underlying transcription available, the longest duration is considered the baseline.

    Parameters
    ----------
    speaker : str
        a speaker name, if desired (defaults to None)
    Returns
    -------
    word_totals : dict
        a dictionary of words and baseline durations
    """
    def baseline_duration(self, speaker = None):
        buckeye = False
        if 'buckeye' in self.corpus_name:
            buckeye = True

        word = getattr(self, self.word_name)
        q = self.query_graph(word)

        allWords = q.all()

        allPhones = self.phone_mean_duration(speaker)

        duration_dict = {}
        word_totals = {}
        for tup in allPhones:
            duration_dict[tup[0]]=tup[1]

        for word in allWords:
            total = 0.0
            if buckeye:
                for phone in re.split("[\. ]", word.transcription):
                    try:
                        total+=duration_dict[phone]
                    except KeyError:
                        print("mistake phone %s"%phone)
            else:
                for phone in word.phone:
                    try:
                        total+=duration_dict[phone.label]
                    except KeyError:
                        print("mistake phone %s"%phone.label)         
            try:         
                if total > word_totals[word.label]:
                    print('replacing %s : %f with %s : %f'%(word.label, word_totals[word.label], word.label, total))
                    word_totals[word.label] = total
                else:
                    continue  
            except KeyError:
                word_totals[word.label] = total
        return word_totals

    """
    Get the mean duration of each syllable

    Returns
    -------
    result : list
        the average duration of each syllable
    """
    def syllable_mean_duration(self): 
        syllable = self.syllable
        return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Average(syllable.duration))


    """
    Gets average syllable durations by speaker

    Returns
    -------
    result : list
        the average duration of each syllable in the corpus, by speaker
    """
    def syllable_mean_duration_with_speaker(self):
        syllable = self.syllable
        self.encode_utterances()
        
        q = self.query_graph(syllable)
        q=q.group_by(syllable.speaker.name.column_name("speaker"), syllable.label.column_name('label'))
        
        result = q.aggregate(Average(syllable.duration))
        
        return result

    """
    Get median duration of each syllable
  
    Returns
    -------
    list
        the median duration of each syllable
    """
    def syllable_median(self): #
        syllable = self.syllable
        return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Median(syllable.duration))
       
    """
    Get the median duration of all the syllables in the corpus

    Returns
    -------
    float
        median duration of all the syllables in the corpus
    """
    def all_syllable_median(self):
        syllable = self.syllable
        return self.query_graph(syllable).aggregate(Median(syllable.duration))
      
    """
    Get the standard deviation of each syllable in a corpus

    Returns
    -------
    result : list
        the standard deviation of each syllable in the corpus
    """
    def syllable_std_dev(self):
        syllable = self.syllable
        return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Stdev(syllable.duration))



    #SPEAKER
    """
    Get the average speech rate for each speaker in a corpus

    Returns
    -------
    result: list 
        the average speech rate by speaker
    """
    def average_speech_rate(self):
  
        word = getattr(self, self.word_name)
        q = self.query_graph(self.utterance)
        print(self.utterance.label)

        return q.group_by(self.utterance.speaker.name.column_name('name')).aggregate(Average(self.utterance.word.rate))

       