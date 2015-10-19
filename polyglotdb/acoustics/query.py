
from polyglotdb.sql.models import Pitch, Formant, SoundFile, Discourse

from .results import PitchResult

class AcousticQuery(object):
    def __init__(self, corpus, graph_query):
        self.corpus = corpus
        self.graph_query = graph_query.times().discourses()
        self.elements = self.graph_query.all()

        self.acoustic_elements = []


    def pitch(self, algorithm):

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
        for i in range(len(self.elements)):
            self.elements[i].__values__ = tuple(list(self.elements[i].__values__) +[self.elements[i].pitch])
        self.elements.columns.append('pitch')
        return self.elements

    def formants(self, *args):
        return self

    def intensity(self, *args):
        return self

    def aggregate(self, *args):
        pass

    def group_by(self, *args):
        return self
