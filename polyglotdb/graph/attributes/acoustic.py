
from ...sql.models import Pitch, Formants, SoundFile, Discourse

from .base import AnnotationAttribute, Attribute

class AcousticAttribute(Attribute):
    output_columns = []
    def __init__(self, annotation):
        self.annotation = annotation
        self.acoustic = True
        self.output_label = None
        self.discourse_alias = annotation.alias + '_discourse'
        self.begin_alias = annotation.alias + '_begin'
        self.end_alias = annotation.alias + '_end'

    def hydrate(self, corpus, discourse, begin, end):
        pass

class PitchAttribute(AcousticAttribute):
    output_columns = ['F0']
    def __init__(self, annotation):
        super(PitchAttribute, self).__init__(annotation)
        self.label = 'pitch'

    def hydrate(self, corpus, discourse, begin, end, aggregation = None):
        """
        Gets all F0 from a discourse

        Parameters
        ----------
        corpus : :class:`~polyglotdb.corpus.CorpusContext`
            The corpus to query
        discourse : str
            the discourse to query
        begin : float
            the start time of the pitch
        end : float
            the end time of the pitch
        aggregation : defaults to None

        Returns
        -------
        data : dict 
            A dictionary with 'F0' as the keys and a dictionary of times and F0 values as the value
         """
        data = {'F0':{}}
        q = corpus.sql_session.query(Pitch).join(SoundFile, Discourse)
        q = q.filter(Pitch.time >= begin, Pitch.time <= end)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Pitch.source == corpus.config.pitch_algorithm)
        results = q.all()
        for line in results:
            data['F0'][line.time] = line.F0
        return data

class FormantAttribute(AcousticAttribute):
    output_columns = ['F1', 'F2', 'F3']
    def __init__(self, annotation):
        super(FormantAttribute, self).__init__(annotation)
        self.label = 'formants'

    def hydrate(self, corpus, discourse, begin, end, aggregation = None):
        """
        Gets all formants from a discourse

        Parameters
        ----------
        corpus : :class:`~polyglotdb.corpus.CorpusContext`
            The corpus to query
        discourse : str
            the discourse to query
        begin : float
            the start time of the pitch
        end : float
            the end time of the pitch
        aggregation : defaults to None

        Returns
        -------
        data : dict 
            A dictionary with 'F1', 'F2', 'F3' as the keys and a dictionary of times and corresponding formant values as the value
         """

        data = {'F1':{}, 'F2':{}, 'F3':{}}
        q = corpus.sql_session.query(Formants).join(SoundFile, Discourse)
        q = q.filter(Formants.time >= begin, Formants.time <= end)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Formants.source == corpus.config.formant_algorithm)
        results = q.all()
        for line in results:
            data['F1'][line.time] = line.F1
            data['F2'][line.time] = line.F2
            data['F3'][line.time] = line.F3
        return data
