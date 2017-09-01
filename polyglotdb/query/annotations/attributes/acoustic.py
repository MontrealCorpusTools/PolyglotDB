from statistics import mean

from .base import AnnotationAttribute


class AcousticAttribute(AnnotationAttribute):
    acoustic = True

    def __init__(self, node, label):
        super(AcousticAttribute, self).__init__(node, label)
        self.output_label = None
        self.discourse_alias = node.alias + '_discourse'
        self.speaker_alias = node.alias + '_speaker'
        self.begin_alias = node.alias + '_begin'
        self.end_alias = node.alias + '_end'
        self.cached_data = None
        self.cached_settings = None
        self.relative = False
        self.relative_time = False

    def __repr__(self):
        return '<AcousticAttribute \'{}\'>'.format(str(self))

    def __getattr__(self, key):
        if key == 'min':
            return Min(self)
        elif key == 'max':
            return Max(self)
        elif key == 'mean':
            return Mean(self)
        elif key == 'track':
            return Track(self)
        elif key == 'sampled_track':
            return SampledTrack(self)
        elif key == 'interpolated_track':
            return InterpolatedTrack(self)

    def hydrate(self, corpus, discourse, begin, end):
        pass


class AggregationAttribute(AcousticAttribute):
    def __init__(self, acoustic_attribute):
        self.attribute = acoustic_attribute
        self.output_label = None

    def __repr__(self):
        return '<AggregationAttribute \'{}\'>'.format(str(self))

    @property
    def node(self):
        return self.attribute.node

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

    def hydrate(self, corpus, discourse, begin, end, channel=0):
        data = self.attribute.hydrate(corpus, discourse, begin, end, channel)
        agg_data = {}
        for i, c in enumerate(self.output_columns):
            gen = [x[self.attribute.output_columns[i]] for x in data.values() if self.attribute.output_columns[i] in x]
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
        return '<MinAttribute \'{}\'>'.format(str(self))

    def function(self, data):
        return min(data)


class Max(AggregationAttribute):
    agg_prefix = 'Max'

    def __repr__(self):
        return '<MaxAttribute \'{}\'>'.format(str(self))

    def function(self, data):
        return max(data)


class Mean(AggregationAttribute):
    agg_prefix = 'Mean'

    def __repr__(self):
        return '<MeanAttribute \'{}\'>'.format(str(self))

    def function(self, data):
        return mean(data)


class Track(AggregationAttribute):
    @property
    def output_columns(self):
        return ['time'] + [x for x in self.attribute.output_columns]

    def hydrate(self, corpus, discourse, begin, end, channel=0):
        data = self.attribute.hydrate(corpus, discourse, begin, end, channel)
        return data

    def __repr__(self):
        return '<Track \'{}\'>'.format(str(self))


class SampledTrack(Track):
    def hydrate(self, corpus, discourse, begin, end, channel=0, num_points=10):
        data = self.attribute.hydrate(corpus, discourse, begin, end, channel, num_points)
        return data

    def __repr__(self):
        return '<SampledTrack \'{}\'>'.format(str(self))


class InterpolatedTrack(Track):
    def __init__(self, *args, **kwargs):
        super(InterpolatedTrack, self).__init__(*args, **kwargs)
        self.num_points = 10

    def __repr__(self):
        return '<InterpolatedTrack \'{}\'>'.format(str(self))

    def hydrate(self, corpus, discourse, begin, end, channel=0):
        from scipy import interpolate
        data = self.attribute.hydrate(corpus, discourse, begin, end, channel, padding=0.01)
        if self.attribute.relative_time:
            duration = 1
            begin = 0
        else:
            duration = end - begin
        time_step = duration / (self.num_points - 1)

        new_data = {begin + x * time_step: dict() for x in range(0, self.num_points)}
        x = sorted(data.keys())
        undef_regions = []
        for i, x1 in enumerate(x):
            if i != len(x) - 1:
                if x[i + 1] - x1 > 0.015:
                    undef_regions.append((x1, x[i + 1]))
        for o in self.attribute.output_columns:
            y = [data[x1][o] for x1 in x]
            if len(y) > 1:
                f = interpolate.interp1d([float(x1) for x1 in x], y)
            for k in new_data.keys():
                if len(y) < 2:
                    new_data[k][o] = None
                    continue
                for r in undef_regions:
                    if k > r[0] and k < r[1]:
                        new_data[k][o] = None
                        break
                else:
                    try:
                        new_data[k][o] = f([k])[0]
                    except ValueError:
                        new_data[k][o] = None
        return new_data


class PitchAttribute(AcousticAttribute):
    def __init__(self, node, relative=False):
        super(PitchAttribute, self).__init__(node, 'pitch')
        self.relative = relative
        self.output_columns = ['F0']
        if relative:
            self.label += '_relative'
            self.output_columns[0] += '_relative'

    def __repr__(self):
        return '<PitchAttribute \'{}\'>'.format(str(self))

    def hydrate(self, corpus, discourse, begin, end, channel=0, num_points=0, padding=0):
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

        if self.cached_settings == (discourse, begin, end, channel, self.relative, num_points):
            data = self.cached_data
        else:
            data = {}

            begin -= padding
            end += padding
            results = corpus.get_pitch(discourse, begin, end, channel=channel, relative=self.relative,
                                       num_points=num_points, relative_time=self.relative_time)
            for line in results:
                data[line[0]] = {self.output_columns[0]: line[1]}
                self.cached_settings = (discourse, begin, end, channel, self.relative, num_points)
                self.cached_data = data
        return data


class IntensityAttribute(AcousticAttribute):
    def __init__(self, node, relative=False):
        super(IntensityAttribute, self).__init__(node, 'intensity')
        self.relative = relative
        self.output_columns = ['Intensity']
        if relative:
            self.label += '_relative'
            self.output_columns[0] += '_relative'

    def __repr__(self):
        return '<IntensityAttribute \'{}\'>'.format(str(self))

    def hydrate(self, corpus, discourse, begin, end, channel=0, num_points=0, padding=0):
        """
        Gets all Intensity from a discourse

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
            A dictionary with 'Intensity' as the keys and a dictionary of times and F0 values as the value
         """

        if self.cached_settings == (discourse, begin, end, channel):
            data = self.cached_data
        else:
            data = {}
            begin -= padding
            end += padding
            results = corpus.get_intensity(discourse, begin, end, channel=channel, relative=self.relative,
                                           relative_time=self.relative_time)
            for line in results:
                data[line[0]] = {self.output_columns[0]: line[1]}
            self.cached_settings = (discourse, begin, end, channel, self.relative)
            self.cached_data = data
        return data


class FormantAttribute(AcousticAttribute):
    def __init__(self, node, relative=False):
        super(FormantAttribute, self).__init__(node, 'formants')
        self.output_columns = ["F1", "F2", "F3", "B1", "B2", "B3"]
        self.relative = relative
        if relative:
            self.label += '_relative'
            for i in range(6):
                self.output_columns[i] += '_relative'

    def __repr__(self):
        return '<FormantAttribute \'{}\'>'.format(str(self))

    def hydrate(self, corpus, discourse, begin, end, channel=0, num_points=0,padding=0):
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
        if self.cached_settings == (discourse, begin, end, channel):
            data = self.cached_data
        else:
            data = {}
            begin -= padding
            end += padding
            results = corpus.get_formants(discourse, begin, end, channel=channel, relative=self.relative,
                                          relative_time=self.relative_time)
            for line in results:
                data[line[0]] = {self.output_columns[i]: line[i + 1] for i in range(6)}
            self.cached_settings = (discourse, begin, end, channel, self.relative)
            self.cached_data = data
        return data
