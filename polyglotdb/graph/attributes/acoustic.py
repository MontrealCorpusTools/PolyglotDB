
from ...sql.models import Pitch, Formants, SoundFile, Discourse

from .base import AnnotationAttribute, Attribute

class AcousticAttribute(Attribute):
    def __init__(self, annotation, corpus):
        self.annotation = annotation
        self.corpus = corpus
        self.acoustic = True
        self.output_label = None

    def hydrate(self, discourse, begin, end):
        pass

class PitchAttribute(AcousticAttribute):
    def __init__(self, annotation, corpus):
        self.label = 'pitch'
        super(PitchAttribute, self).__init__(annotation, corpus)

    def hydrate(self, discourse, begin, end, aggregation = None):
        data = {}
        q = self.corpus.sql_session.query(Pitch).join(SoundFile, Discourse)
        q = q.filter(Pitch.time >= begin, Pitch.time <= end)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Pitch.source == self.corpus.config.pitch_algorithm)
        results = q.all()
        for line in results:
            data[line.time] = line.F0
        return data

class FormantAttribute(AcousticAttribute):
    def __init__(self, annotation, corpus):
        self.label = 'formants'
        super(FormantAttribute, self).__init__(annotation, corpus)

    def hydrate(self, discourse, begin, end, aggregation = None):
        data = {}
        q = self.corpus.sql_session.query(Formants).join(SoundFile, Discourse)
        q = q.filter(Formants.time >= begin, Formants.time <= end)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Formants.source == self.corpus.config.formant_algorithm)
        results = q.all()
        for line in results:
            data[line.time] = (line.F1, line.F2, line.F3)
        return data
