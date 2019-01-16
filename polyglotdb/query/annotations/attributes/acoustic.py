from statistics import mean, stdev, median
from decimal import Decimal

from .base import AnnotationAttribute


class AcousticAttribute(AnnotationAttribute):
    acoustic = True

    def __init__(self, node, label):
        super(AcousticAttribute, self).__init__(node, label)
        self.output_label = None
        self.discourse_alias = node.alias + '_discourse'
        self.utterance_alias = node.alias + '_utterance'
        self.speaker_alias = node.alias + '_speaker'
        self.begin_alias = node.alias + '_begin'
        self.end_alias = node.alias + '_end'
        self.cached_data = None
        self.cached_settings = None
        self.relative = False
        self.relative_time = False

    def __repr__(self):
        return '<AcousticAttribute \'{}\'>'.format(str(self))

    def __str__(self):
        return "{}.{}".format(self.node, self.label)

    def __getattr__(self, key):
        if key == 'min':
            return Min(self)
        elif key == 'max':
            return Max(self)
        elif key == 'mean':
            return Mean(self)
        elif key == 'median':
            return Median(self)
        elif key == 'stdev':
            return Stdev(self)
        elif key == 'track':
            return Track(self)
        elif key == 'interpolated_track':
            return InterpolatedTrack(self)
        raise AttributeError('AcousticAttributes have no property {}'.format(key))

    @property
    def output_columns(self):
        return sorted(x[0] for x in self.node.hierarchy.acoustic_properties[self.label])

    def hydrate(self, corpus, utterance_id, begin, end, padding=0):
        """
        Gets all formants from a discourse

        Parameters
        ----------
        corpus : :class:`~polyglotdb.corpus.CorpusContext`
            The corpus to query
        utterance_id : str
            The ID of the utterance
        begin : float
            The start time of the annotation
        end : float
            The end time of the annotation
        padding : float
            Extra time at begin and end

        Returns
        -------
        :class:`~polyglotdb.acoustics.classes.Track`
            A Track object with formant TimePoints
         """
        utterance_data = self.cache[utterance_id]
        if self.node.node_type == 'utterance':
            return utterance_data
        if padding:
            begin -= padding
            end += padding
        return utterance_data.slice(begin, end)


class AggregationAttribute(AcousticAttribute):
    agg_prefix = ''

    def __init__(self, acoustic_attribute):
        self.attribute = acoustic_attribute
        self.output_label = None
        self.label = self.agg_prefix

    def __repr__(self):
        return '<AggregationAttribute \'{}\'>'.format(str(self))

    @property
    def node(self):
        return self.attribute.node

    @property
    def utterance_alias(self):
        return self.attribute.utterance_alias

    @utterance_alias.setter
    def utterance_alias(self, value):
        self.attribute.utterance_alias = value

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
        if self.output_label is not None and len(self.attribute.output_columns) == 1:
            return [self.output_label]
        return ['{}_{}'.format(self.agg_prefix, x) for x in self.attribute.output_columns]

    def hydrate(self, corpus, utterance_id, begin, end):
        data = self.attribute.hydrate(corpus, utterance_id, begin, end)
        agg_data = {}
        for i, c in enumerate(self.output_columns):
            gen = [x[self.attribute.output_columns[i]] for x in data if self.attribute.output_columns[i] in x]
            gen = [x for x in gen if x is not None]
            if not gen:
                agg_data[c] = None
            else:
                if gen:
                    agg_data[c] = self.function(gen)
                else:
                    agg_data[c] = None
        return agg_data


class Min(AggregationAttribute):
    agg_prefix = 'Min'

    def __repr__(self):
        return '<Min \'{}\'>'.format(str(self))

    def function(self, data):
        return min(data)


class Max(AggregationAttribute):
    agg_prefix = 'Max'

    def __repr__(self):
        return '<Max \'{}\'>'.format(str(self))

    def function(self, data):
        return max(data)


class Mean(AggregationAttribute):
    agg_prefix = 'Mean'

    def __repr__(self):
        return '<Mean \'{}\'>'.format(str(self))

    def function(self, data):
        return mean(data)


class Median(AggregationAttribute):
    agg_prefix = 'Median'

    def __repr__(self):
        return '<Median \'{}\'>'.format(str(self))

    def function(self, data):
        return median(data)


class Stdev(AggregationAttribute):
    agg_prefix = 'Stdev'

    def __repr__(self):
        return '<Stdev \'{}\'>'.format(str(self))

    def function(self, data):
        if len(data) > 1:
            return stdev(data)
        return None


class Track(AggregationAttribute):
    @property
    def output_columns(self):
        return ['time'] + [x for x in self.attribute.output_columns]

    def hydrate(self, corpus, utterance_id, begin, end):
        data = self.attribute.hydrate(corpus, utterance_id, begin, end)
        if self.attribute.relative_time:
            begin = Decimal(begin)
            end = Decimal(end)
            duration = end - begin
            for p in data:
                p.time = (p.time - begin) / duration
        return data

    def __repr__(self):
        return '<Track \'{}\'>'.format(str(self))


class InterpolatedTrack(Track):
    def __init__(self, *args, **kwargs):
        super(InterpolatedTrack, self).__init__(*args, **kwargs)
        self.num_points = 10

    def __repr__(self):
        return '<InterpolatedTrack \'{}\'>'.format(str(self))

    def hydrate(self, corpus, utterance_id, begin, end):
        from ....acoustics.classes import Track as RawTrack, TimePoint as RawTimePoint
        from scipy import interpolate
        data = self.attribute.hydrate(corpus, utterance_id, begin, end, padding=0.01)

        duration = end - begin
        time_step = duration / (self.num_points - 1)

        new_times = [begin + x * time_step for x in range(0, self.num_points)]
        x = data.times()
        undef_regions = []
        for i, x1 in enumerate(x):
            if i != len(x) - 1:
                if x[i + 1] - x1 > 0.015:
                    undef_regions.append((x1, x[i + 1]))
        new_data = RawTrack()
        for o in self.attribute.output_columns:
            y = [data[x1][o] for x1 in x]
            if len(y) > 1:
                f = interpolate.interp1d([float(x1) for x1 in x], y)
            for k in new_times:
                out_time = k
                if self.attribute.relative_time:
                    out_time = (k - begin) / duration
                point = RawTimePoint(out_time)
                if len(y) < 2:
                    point.add_value(o, None)
                else:
                    for r in undef_regions:
                        if k > r[0] and k < r[1]:
                            point.add_value(o, None)
                            break
                    else:
                        try:
                            point.add_value(o, f([k])[0])
                        except ValueError:
                            point.add_value(o, None)
                new_data.add(point)
        return new_data
