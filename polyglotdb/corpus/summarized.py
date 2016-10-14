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
        if not self.hierarchy.has_type_property('utterance','label'):
            self.encode_utterances()
        if speaker is not None:
            q = self.query_graph(phone).filter(phone.speaker.name==speaker)
        else:
            q = self.query_graph(phone)

       # q=q.group_by(phone.label.column_name('label'))

       # result = q.aggregate(Average(phone.duration))
        statement = "MATCH (p:phone:{corpus_name}) RETURN p.label as phone, avg(p.end - p.begin) as average_duration".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)

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
        if not self.hierarchy.has_type_property('utterance','label'):
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
        #result = self.query_graph(phone).group_by(phone.label.column_name('label')).aggregate(Stdev(phone.duration))#.filter(phone.label==to_find)
        statement = "MATCH (p:phone:{corpus_name}) RETURN p.label as phone, stdev(p.end - p.begin) as standard_deviation".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)
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
        statement = "MATCH (p:phone:{corpus_name}) RETURN p.label as phone, percentileDisc(p.end - p.begin, .5) as median_duration".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)
        return result
        #self.query_graph(phone).group_by(phone.label.column_name('label')).aggregate(Median(phone.duration))#.filter(phone.label == to_find)



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
        #result = self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Average(word.duration))#.filter(word.label==to_find)
        statement = "MATCH (p:word:{corpus_name}) RETURN p.label as word, avg(p.end - p.begin) as average_duration".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)
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
        if not self.hierarchy.has_type_property('utterance','label'):
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
        statement = "MATCH (p:word:{corpus_name}) RETURN p.label as word, percentileDisc(p.end - p.begin, .5) as median_duration".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)
        return result
        #self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Median(word.duration))#.filter(word.label == to_find)


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
        statement = "MATCH (p:word:{corpus_name}) RETURN p.label as word, stdev(p.end - p.begin) as standard_deviation".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)

        return result
        #self.query_graph(word).group_by(word.label.column_name('label')).aggregate(Stdev(word.duration))#.filter(word.label==to_find)



    def baseline_duration(self, annotation, speaker = None):
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
        
        index = 'label'
        word = getattr(self, self.word_name)
        phone = getattr(self,self.phone_name)
        # if annotation == 'word':
        #     annotation = word
        if annotation == 'utterance':
            ## TODO: find a good key for utterances (labels too long anyway and are None)
            index = 'id'
            if not self.hierarchy.has_type_property('utterance','label'):
                raise(AttributeError('Annotation type \'{}\' not found.'.format(annotation)))
        if annotation == 'syllable':
            if not self.hierarchy.has_type_property('syllable','label'):
                raise(AttributeError('Annotation type \'{}\' not found.'.format(annotation)))

        statement = '''
MATCH (m:phone:{corpus_name}) 
with m.{index} as l, avg(m.end-m.begin) as dur 
with l,dur match (p:phone:{corpus_name}) 
where p.{index} = l set p.average_duration = dur 
with p as phone  match(n:{higher_annotation}:{corpus_name}) where phone.begin>=n.begin and phone.end<=n.end
with n,phone with n, n.{index} as l, sum(phone.average_duration) as baseline 
set n.baseline_duration = baseline return n.{index}, n.baseline_duration'''.format(higher_annotation=annotation,\
 corpus_name=self.corpus_name, index = index)
        
        if speaker is not None:
            prefix = '''MATCH (speaker:Speaker:{corpus_name}) 
            where speaker.name = '{speaker}' with speaker'''.format(corpus_name=self.corpus_name,speaker=speaker)
            statement = prefix+statement

        res = self.execute_cypher(statement)     
        result = {}
        for c in res:
            result.update({c[0]:c[1]})
        return result

    def syllable_mean_duration(self):
        """
        Get the mean duration of each syllable

        Returns
        -------
        result : list
            the average duration of each syllable
        """
        syllable = self.syllable
        #return self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Average(syllable.duration))
        statement = "MATCH (p:syllable:{corpus_name}) RETURN p.label as syllable, avg(p.end - p.begin) as average_duration".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)
        return result

    def syllable_mean_duration_with_speaker(self):
        """
        Gets average syllable durations by speaker

        Returns
        -------
        result : list
            the average duration of each syllable in the corpus, by speaker
        """
        syllable = self.syllable
        if not self.hierarchy.has_type_property('utterance','label'):
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
        statement = "MATCH (p:syllable:{corpus_name}) RETURN p.label as syllable, percentileDisc(p.end - p.begin, .5) as median_duration".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)
        return result
        #self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Median(syllable.duration))


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

        statement = "MATCH (p:syllable:{corpus_name}) RETURN p.label as syllable, stdev(p.end - p.begin) as standard_deviation".format(corpus_name = self.corpus_name)


        result = []
        res = self.execute_cypher(statement)
        for item in res:
            result.append(item)

        return result
        #self.query_graph(syllable).group_by(syllable.label.column_name('label')).aggregate(Stdev(syllable.duration))



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

    def make_dict(self, data, speaker = False):
        """
        turn data results into a dictionary for encoding

        Parameters
        ----------

        data : list
            a list returned by cypher

        Returns
        -------
        finaldict : dict
            a dictionary in the format for enrichment

        """
        finalDict = {}
        if not speaker:
            if type(data) == list and len(data[0])==2:
                for i,r in enumerate(data):
                    finalDict.update({r[0]:{str(data[1].keys()[1]):r[1]}})
            else:
                for r in data.keys():
                    finalDict.update({r : {'baseline_duration': data[r]}})

        if speaker:
            keys = data[0].keys()
            speaker = data[0].values()[0]
            prop = keys[2]
            firstDict = {x['label']:x[prop] for x in data  }
            speakerDict = self.make_speaker_annotations_dict(firstDict, speaker, prop)
            return speakerDict
        return finalDict


    def encode_measure(self, measure):

        """
        encode the data into the graph

        Parameters
        ----------
        measure: str
            desired measure to encode

        """
        res = None
        speaker = False
        if measure == 'word_median':
            data_type = 'word'
            res = self.word_median()
        elif measure == 'all_word_median':
            data_type = 'word'
            res = self.all_word_median()
        elif measure == 'word_mean_duration':
            data_type = 'word'
            res = self.word_mean_duration()
        elif measure == 'word_std_dev':
            data_type = 'word'
            res = self.word_std_dev()
        elif measure == 'baseline_duration_utterance':
            data_type = 'utterance'
            res = self.baseline_duration('utterance')
        elif measure == 'baseline_duration_word':
            data_type = 'word'
            res = self.baseline_duration('word')
        elif measure == 'baseline_duration_syllable':
            data_type = 'syllable'
            res = self.baseline_duration('syllable')
        elif measure == 'phone_mean':
            data_type = 'phone'
            res = self.phone_mean_duration()
        elif measure == 'phone_median':
            data_type = 'phone'
            res = self.phone_median()
        elif measure == 'phone_std_dev':
            data_type = 'phone'
            res = self.phone_std_dev()
        elif measure == 'all_word_median':
            res = self.all_word_median()
        elif measure == 'phone_mean_duration_with_speaker':
            data_type = 'speaker'
            res = self.phone_mean_duration_with_speaker()
            speaker = True
        elif measure == 'word_mean_by_speaker':
            data_type = 'speaker'
            res = self.word_mean_duration_with_speaker()
            speaker = True
        elif measure == 'all_phone_median':
            data_type = 'phone'
            res = self.all_phone_median()
        elif measure == 'syllable_mean':
            data_type = 'syllable'
            res = self.syllable_mean_duration()
        elif measure == 'syllable_median':
            data_type = 'syllable'
            res = self.syllable_median()
        elif measure == 'syllable_std_dev':
            data_type = 'syllable'
            res = self.syllable_std_dev()
        elif measure == 'mean_speech_rate':
            data_type = 'speaker'
            res = self.average_speech_rate()
            speaker = True

        else:
            print("error")



        dataDict = self.make_dict(res,speaker)

        if data_type == 'word':
            self.enrich_lexicon(dataDict)
        elif data_type == 'phone':
            self.enrich_features(dataDict)
        elif data_type == 'syllable':
            self.enrich_syllables(dataDict)
        elif data_type == 'speaker':
            self.enrich_speaker_annotations(dataDict)
        elif data_type == 'utterance':
            self.enrich_utterances(dataDict)

