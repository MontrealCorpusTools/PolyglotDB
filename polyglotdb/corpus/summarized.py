import math
from .base import BaseContext
from polyglotdb.graph.func import *
import re

class SummarizedContext(BaseContext):

    
    def phone_mean_duration(self, speaker = None):
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
        phone = getattr(self, self.phone_name)
        self.encode_utterances()
        if speaker is not None:
            q = self.query_graph(phone).filter(phone.speaker.name==speaker)
        else:
            q = self.query_graph(phone)

        q=q.group_by(phone.label.column_name('label'))
    
        result = q.aggregate(Average(phone.duration))
      
        return result
    
    

    def phone_mean_duration_with_speaker(self):
        """
        Gets average phone durations by speaker

        Returns
        -------
        result : list
            the average duration of each phone in the corpus, by speaker
        """
        phone = getattr(self, self.phone_name)
        self.encode_utterances()
        
        q = self.query_graph(phone)
        q=q.group_by(phone.speaker.name.column_name("speaker"), phone.label.column_name('label'))
        
        result = q.aggregate(Average(phone.duration))
        
        return result

    
    def phone_std_dev(self):
        """
        Get the standard deviation of each phone in a corpus

        Returns
        -------
        result : list
            the standard deviation of each phone in the corpus
        """
        phone = getattr(self, self.phone_name)
        result = self.query_graph(phone).group_by(phone.label.column_name('label')).aggregate(Stdev(phone.duration))#.filter(phone.label==to_find)

        return result

    
    def all_phone_median(self):
        """
        Get the median duration of all the phones in the corpus

        Returns
        -------
        float
            median duration of all the phones in the corpus
        """
        phone = getattr(self, self.phone_name)
        return self.query_graph(phone).aggregate(Median(phone.duration))


    
    def phone_median(self):
        """
        Get the median duration of each phone in a corpus

        Returns
        -------
        result : list
            the median duration of each phone in the corpus
        """
        phone = getattr(self, self.phone_name)
        return self.query_graph(phone).group_by(phone.label.column_name('label')).aggregate(Median(phone.duration))#.filter(phone.label == to_find)
      
    

    def get_mean_duration(self, type):
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
    
    def word_mean_duration(self):
        """
        Get the mean duration of each word

        Returns
        -------
        result : list
            the average duration of each word
        """
        word = getattr(self,self.word_name)
        result = self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Average(word.duration))#.filter(word.label==to_find)
       
        return result


    

    def word_mean_duration_with_speaker(self):
        """
        Gets average word durations by speaker

        Returns
        -------
        result : list
            the average duration of each word in the corpus, by speaker
        """
        word = getattr(self, self.word_name)
        self.encode_utterances()
        
        q = self.query_graph(word)
      
        #    q = q.columns()
        q=q.group_by(word.speaker.name.column_name("speaker"), word.label.column_name('label'))
        
        result = q.aggregate(Average(word.duration))
        
        return result
    
    def word_median(self):
        """
        Get the median duration of each word

        Returns
        -------
        list
            the median duration of each word
        """
        word = getattr(self, self.word_name)
        return self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Median(word.duration))#.filter(word.label == to_find)
      
    
    def all_word_median(self):
        """
        Get the median duration of all the words in the corpus  

        Returns
        -------
        float
            median duration of all the words in the corpus
        """
        word = getattr(self, self.word_name)
        return self.query_graph(word).aggregate(Median(word.duration))

    
    def word_std_dev(self):
        """
        Get the standard deviation of each word in a corpus
    
        Returns
        -------
        result : list
            the standard deviation of each word in the corpus
        """
        word = getattr(self, self.word_name)
        return self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Stdev(word.duration))#.filter(word.label==to_find)


    
    def baseline_duration(self, speaker = None):
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
                        pass
            else:
                for phone in word.phone:
                    try:
                        total+=duration_dict[phone.label]
                    except KeyError:
                        pass        
            try:         
                if total > word_totals[word.label]:
                    #print('replacing %s : %f with %s : %f'%(word.label, word_totals[word.label], word.label, total))
                    word_totals[word.label] = total
                else:
                    continue  
            except KeyError:
                word_totals[word.label] = total
        return word_totals

    
    def syllable_mean_duration(self): 
        """
        Get the mean duration of each syllable

        Returns
        -------
        result : list
            the average duration of each syllable
        """
        syllable = self.syllable
        return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Average(syllable.duration))


    
    def syllable_mean_duration_with_speaker(self):
        """
        Gets average syllable durations by speaker

        Returns
        -------
        result : list
            the average duration of each syllable in the corpus, by speaker
        """
        syllable = self.syllable
        self.encode_utterances()
        
        q = self.query_graph(syllable)
        q=q.group_by(syllable.speaker.name.column_name("speaker"), syllable.label.column_name('label'))
        
        result = q.aggregate(Average(syllable.duration))
        
        return result

    
    def syllable_median(self): 
        """
        Get median duration of each syllable
  
        Returns
        -------
        list
            the median duration of each syllable
        """
        syllable = self.syllable
        return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Median(syllable.duration))
       
    
    def all_syllable_median(self):
        """
        Get the median duration of all the syllables in the corpus

        Returns
        -------
        float
            median duration of all the syllables in the corpus
        """
        syllable = self.syllable
        return self.query_graph(syllable).aggregate(Median(syllable.duration))
      
    
    def syllable_std_dev(self):
        """
        Get the standard deviation of each syllable in a corpus

        Returns
        -------
        result : list
            the standard deviation of each syllable in the corpus
        """
        syllable = self.syllable
        return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Stdev(syllable.duration))



    #SPEAKER
    
    def average_speech_rate(self):
        """
        Get the average speech rate for each speaker in a corpus

        Returns
        -------
        result: list 
            the average speech rate by speaker
        """
  
        word = getattr(self, self.word_name)
        q = self.query_graph(self.utterance)
        

        return q.group_by(self.utterance.speaker.name.column_name('name')).aggregate(Average(self.utterance.word.rate))

       
    def make_dict(self, data):
        """
        turn data results into a dictionary for encoding
        """
        finalDict = {}
        if type(data) == list and len(data[0])==2:
            for i,r in enumerate(data):
                finalDict.update({r[0]:{str(data[1].keys()[1]):r[1]}})
        elif type(data) == list and len(data[0]) == 3:
            for i,r in enumerate(data):
                speaker = r[0]
                word = r[1]
                num = r[2]
                #finalDict.update({str(speaker) : {:}})
        else:
            for r in data.keys():
                finalDict.update({r : {'baseline_duration': data[r]}})   
        return finalDict
    def encode_measure(self, data, data_type):
        """
        encode the data into the graph
        """   
        dataDict = self.make_dict(data)
        if data_type == 'word':
            self.enrich_lexicon(dataDict)
        elif data_type == 'phone':
            self.enrich_features(dataDict)