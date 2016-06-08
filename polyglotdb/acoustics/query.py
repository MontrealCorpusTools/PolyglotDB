
from ..sql.models import Pitch, Formants, SoundFile, Discourse

from .results import PitchResult, FormantsResult

class AcousticQuery(object):
    def __init__(self, corpus, graph_query):
        self.corpus = corpus
        self.graph_query = graph_query.times().discourses()
        self.elements = self.graph_query.all()

        self.acoustic_elements = []


    def pitch(self, algorithm):
        """ 
        finds the correct file, then adds the pitch to it 

        Parameters
        ----------
        algorithm : str
            the algorithm to be used for finding pitch
        """
        for i, element in enumerate(self.elements):
            begin, end = element.begin, element.end
            q = self.corpus.sql_session.query(Pitch).join(SoundFile, Discourse)
            q = q.filter(Pitch.time >= begin, Pitch.time <= end)
            q = q.filter(Discourse.name == element.discourse)
            q = q.filter(Pitch.source == algorithm)
            self.elements[i].pitch = PitchResult(q.all())
        self.acoustic_elements.append('pitch')
        return self

    def max(self):
        """
        for each element, get the maximum acoustic element and add it to __values__

        Returns
        -------
        self.elements

         """
        for e in self.acoustic_elements:
            name = 'max_{}'.format(e)
            for i in range(len(self.elements)):
                r = getattr(self.elements[i], e)
                max_element = r.max()
                self.elements[i].__values__ = tuple(list(self.elements[i].__values__) +[max_element])
                setattr(self.elements[i], name, max_element)
            self.elements.columns.append(name)
        return self.elements

    def all(self):
        """ 
        add the pitch to each element's __values__ tuple
        
        Returns
        -------
        self.elements
        """ 
        for i in range(len(self.elements)):
            self.elements[i].__values__ = tuple(list(self.elements[i].__values__) +[self.elements[i].pitch])
        self.elements.columns.append('pitch')
        return self.elements

    def formants(self, algorithm):
        """ 
        finds the correct file, then adds the formants to it 

        Parameters
        ----------
        algorithm : str
            the algorithm to be used for finding the formants

        """
        for i, element in enumerate(self.elements):
            begin, end = element.begin, element.end
            q = self.corpus.sql_session.query(Formants).join(SoundFile, Discourse)
            q = q.filter(Formants.time >= begin, Formants.time <= end)
            q = q.filter(Discourse.name == element.discourse)
            q = q.filter(Formants.source == algorithm)
            self.elements[i].formants = FormantsResult(q.all())
        self.acoustic_elements.append('formants')
        return self

    def intensity(self, *args):
        return self

    def aggregate(self, *args):
        pass

    def group_by(self, *args):
        return self
