
from statistics import mean
from sqlalchemy import text

from ...sql.models import Pitch, Formants, SoundFile, Discourse

from .base import AnnotationAttribute, Attribute

class AcousticAttribute(Attribute):
    acoustic = True
    def __init__(self, annotation):
        self.annotation = annotation
        self.output_label = None
        self.discourse_alias = annotation.alias + '_discourse'
        self.speaker_alias = annotation.alias + '_speaker'
        self.begin_alias = annotation.alias + '_begin'
        self.end_alias = annotation.alias + '_end'
        self.cached_data = None
        self.cached_settings = None

    def __getattr__(self, key):
        if key == 'min':
            return Min(self)
        elif key == 'max':
            return Max(self)
        elif key == 'mean':
            return Mean(self)

    def hydrate(self, corpus, discourse, begin, end):
        pass

class AggregationAttribute(AcousticAttribute):
    def __init__(self, acoustic_attribute):
        self.attribute = acoustic_attribute
        self.output_label = None
        self.ignore_negative = False
        if isinstance(self.attribute, PitchAttribute):
            self.ignore_negative = True

    @property
    def annotation(self):
        return self.attribute.annotation

    @property
    def discourse_alias(self):
        return self.attribute.discourse_alias

    @discourse_alias.setter
    def discourse_alias(self, value):
        self.attribute.discourse_alias = value

    @property
    def speaker_alias(self):
        return self.attribute.speaker_alias

    @speaker_alias.setter
    def speaker_alias(self, value):
        self.attribute.speaker_alias = value

    @property
    def begin_alias(self):
        return self.attribute.begin_alias

    @begin_alias.setter
    def begin_alias(self, value):
        self.attribute.begin_alias = value

    @property
    def end_alias(self):
        return self.attribute.end_alias

    @end_alias.setter
    def end_alias(self, value):
        self.attribute.end_alias = value

    @property
    def output_columns(self):
        return ['{}_{}'.format(self.agg_prefix, x) for x in self.attribute.output_columns]

    def hydrate(self, corpus, discourse, begin, end, channel = 0):
        data = self.attribute.hydrate(corpus, discourse, begin, end, channel)
        agg_data = {}
        for i, c in enumerate(self.output_columns):
            d = data[self.attribute.output_columns[i]]
            if not d:
                agg_data[c] = None
            else:
                gen = [x for x in d.values() if x is not None]
                if self.ignore_negative:
                    gen = [x for x in gen if x > 0]
                if gen:
                    agg_data[c] = self.function(gen)
                else:
                    agg_data[c] = None
        return agg_data

class Min(AggregationAttribute):
    agg_prefix = 'Min'

    def function(self, data):
        return min(data)

class Max(AggregationAttribute):
    agg_prefix = 'Max'

    def function(self, data):
        return max(data)

class Mean(AggregationAttribute):
    agg_prefix = 'Mean'

    def function(self, data):
        return mean(data)

class PitchAttribute(AcousticAttribute):
    output_columns = ['F0']
    def __init__(self, annotation):
        super(PitchAttribute, self).__init__(annotation)
        self.label = 'pitch'

    def hydrate(self, corpus, discourse, begin, end, channel = 0):
        if self.cached_settings == (discourse, begin, end, channel):
            data = self.cached_data
        else:
            data = {'F0':{}}
            q = corpus.sql_session.query(Pitch.time, Pitch.F0).join(SoundFile, Discourse)
            q = q.filter(Pitch.time >= begin, Pitch.time <= end)
            q = q.filter(Discourse.name == discourse)
            q = q.filter(Pitch.source == corpus.config.pitch_algorithm)
            q = q.filter(Pitch.channel == channel)
            results = q.all()
            for line in results:
                data['F0'][line[0]] = line[1]
            self.cached_settings = (discourse, begin, end, channel)
            self.cached_data = data
        return data

class FormantAttribute(AcousticAttribute):
    output_columns = ['F1', 'F2', 'F3']
    def __init__(self, annotation):
        super(FormantAttribute, self).__init__(annotation)
        self.label = 'formants'

    def hydrate(self, corpus, discourse, begin, end, channel = 0):
        if self.cached_settings == (discourse, begin, end, channel):
            data = self.cached_data
        else:
            data = {'F1':{}, 'F2':{}, 'F3':{}}
            q = corpus.sql_session.query(Formants).join(SoundFile, Discourse)
            q = q.filter(Formants.time >= begin, Formants.time <= end)
            q = q.filter(Discourse.name == discourse)
            q = q.filter(Formants.channel == channel)
            q = q.filter(Formants.source == corpus.config.formant_algorithm)
            results = q.all()
            for line in results:
                data['F1'][line.time] = line.F1
                data['F2'][line.time] = line.F2
                data['F3'][line.time] = line.F3
            self.cached_settings = (discourse, begin, end, channel)
            self.cached_data = data
        return data
