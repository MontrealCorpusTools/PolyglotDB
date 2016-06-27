import math
from .base import BaseContext
from polyglotdb.graph.func import *


class SummarizedContext(BaseContext):

 
    def hardcode_mean_duration(self):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone).filter(phone.label=='ah')
        result = q.aggregate(Average(phone.duration))
        print(result)
        return result

    #phones
    """
    Get the mean duration of a specific phone in a corpus

    Parameters
    ----------
    to_find : str
        the label of the phone 

    Returns
    -------
    result : float
        the average duration of the phone in the corpus
    """
    def phone_mean_duration(self, to_find):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone).filter(phone.label==to_find)
        result = q.aggregate(Average(phone.duration))
        return result

    """
    Get the standard deviation of a specific phone in a corpus

    Parameters
    ----------
    to_find : str
        the label of the phone 

    Returns
    -------
    result : float
        the standard deviation of the phone in the corpus
    """
    def phone_std_dev(self, to_find):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone).filter(phone.label==to_find)

        allPhones = q.all()
        avg = q.aggregate(Average(phone.duration))
        allDiffs = []
        for phone in allPhones:
            x = phone.duration
            diff = x - avg
            diffSQ = math.pow(diff,2)
            allDiffs.append(diffSQ)
        res = sum(allDiffs)/len(allPhones)
        result = math.sqrt(res)
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
        q = self.query_graph(phone)
        phone_durations = []
        allPhones = q.all()
        for phone in allPhones:
            phone_durations.append(phone.duration)
        phone_durations = sorted(phone_durations)
        if len(phone_durations) == 0:
            return 0.0
        return (phone_durations[math.floor(len(phone_durations)/2)]+phone_durations[math.ceil(len(phone_durations)/2)])/2


    """
    Get the median duration of a specific phone in a corpus

    Parameters
    ----------
    to_find : str
        the label of the phone 

    Returns
    -------
    result : float
        the median duration of the phone in the corpus
    """
    def phone_median(self, to_find):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone).filter(phone.label == to_find)
        phone_durations = []
        allPhones = q.all()
        for phone in allPhones:
            phone_durations.append(phone.duration)
        phone_durations = sorted(phone_durations)
        if len(phone_durations) == 0:
            return 0.0        
        return (phone_durations[math.floor(len(phone_durations)/2)]+phone_durations[math.ceil(len(phone_durations)/2)])/2

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
        return result

    #words
    """
    Get the mean duration of a specific word

    Parameters
    ----------
    to_find : str
        the label of the word

    Returns
    -------
    result : float
        the average duration of the word
    """
    def word_mean_duration(self, to_find):
        word = getattr(self,self.word_name)
        q = self.query_graph(word).filter(word.label==to_find)
        result = q.aggregate(Average(word.duration))        
        return result


    """
    Get the median duration of a specific word

    Parameters
    ----------
    to_find : str
        the label of the word

    Returns
    -------
    loat
        the median duration of the word
    """
    def word_median(self, to_find):
        word = getattr(self, self.word_name)
        q = self.query_graph(word).filter(word.label == to_find)
        word_durations = []
        allWords = q.all()
        for word in allWords:
            word_durations.append(word.duration)
        word_durations = sorted(word_durations)
        if len(word_durations) == 0:
            return 0.0
        return (word_durations[math.floor(len(word_durations)/2)]+word_durations[math.ceil(len(word_durations)/2)])/2

    """
    Get the median duration of all the words in the corpus

    Returns
    -------
    float
        median duration of all the words in the corpus
    """
    def all_word_median(self):
        word = getattr(self, self.word_name)
        q = self.query_graph(word)
        word_durations = []
        allWords = q.all()
        for word in allWords:
            word_durations.append(word.duration)
        word_durations = sorted(word_durations)
        if len(word_durations) == 0:
            return 0.0
        return (word_durations[math.floor(len(word_durations)/2)]+word_durations[math.ceil(len(word_durations)/2)])/2


    """
    Get the standard deviation of a specific word in a corpus

    Parameters
    ----------
    to_find : str
        the label of the word 

    Returns
    -------
    result : float
        the standard deviation of the word in the corpus
    """
    def word_std_dev(self, to_find):
        word = getattr(self, self.word_name)
        q = self.query_graph(word).filter(word.label==to_find)

        allWords = q.all()
        avg = q.aggregate(Average(word.duration))
        allDiffs = []
        for word in allWords:
            x = word.duration
            diff = x - avg
            diffSQ = math.pow(diff,2)
            allDiffs.append(diffSQ)
        res = sum(allDiffs)/len(allWords)
        result = math.sqrt(res)
        return result

    #syllables
    """
    Get the mean duration of a specific syllable

    Parameters
    ----------
    to_find : str
        the label of the syllable

    Returns
    -------
    result : float
        the average duration of the syllable
    """
    def syllable_mean_duration(self, to_find): 
        syllable = self.syllable
        q = self.query_graph(syllable).filter(syllable.label==to_find)
        allSyls = q.all()
        result = q.aggregate(Average(syllable.duration))   
        return result


    """
    Get median duration of a specific syllable
    Parameters
    ----------
    to_find : str
        the label of the syllable

    Returns
    -------
    loat
        the median duration of the syllable
    """
    def syllable_median(self, to_find): #
        syllable = self.syllable
        q = self.query_graph(syllable).filter(syllable.label==to_find)
        allSyls = q.all()
        syllable_durations = []
        
        for syllable in allSyls:
            syllable_durations.append(syllable.duration)
            print(syllable.label)
        syllable_durations = sorted(syllable_durations)
        if len(syllable_durations) == 0:
            return 0.0
        return (syllable_durations[math.floor(len(syllable_durations)/2)]+syllable_durations[math.ceil(len(syllable_durations)/2)])/2

    """
    Get the median duration of all the syllables in the corpus

    Returns
    -------
    float
        median duration of all the syllables in the corpus
    """
    def all_syllable_median(self):
        syllable = self.syllable
        q = self.query_graph(syllable)
        syllable_durations = []
        allSyls = q.all()
        for syllable in allSyls:
            syllable_durations.append(syllable.duration)
        syllable_durations = sorted(syllable_durations)
        if len(syllable_durations) == 0:
            return 0.0
        return (syllable_durations[math.floor(len(syllable_durations)/2)]+syllable_durations[math.ceil(len(syllable_durations)/2)])/2


    """
    Get the standard deviation of a specific syllable in a corpus

    Parameters
    ----------
    to_find : str
        the label of the syllable 

    Returns
    -------
    result : float
        the standard deviation of the syllable in the corpus
    """
    def syllable_std_dev(self, to_find):
        syllable = self.syllable
        q = self.query_graph(syllable).filter(syllable.label==to_find)

        allSyls = q.all()
        avg = q.aggregate(Average(syllable.duration))
        allDiffs = []
        for syllable in allSyls:
            x = syllable.duration
            diff = x - avg
            diffSQ = math.pow(diff,2)
            allDiffs.append(diffSQ)
        res = sum(allDiffs)/len(allSyls)
        result = math.sqrt(res)
        return result
