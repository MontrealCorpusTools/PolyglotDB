

from polyglotdb.exceptions import GraphQueryError

from ..base.results import BaseQueryResults, BaseRecord

from .attributes import (HierarchicalAnnotation, SubPathAnnotation,
                         SubAnnotation as QuerySubAnnotation,
                         SpeakerAnnotation, DiscourseAnnotation,
                         Track)

from .models import LinguisticAnnotation, SubAnnotation, Speaker, Discourse


def hydrate_model(r, to_find, to_find_type, to_preload, corpus):
    a = LinguisticAnnotation(corpus)
    a.node = r[to_find]
    a.type_node = r[to_find_type]
    a._preloaded = True
    for pre in to_preload:
        if isinstance(pre, DiscourseAnnotation):
            pa = Discourse(corpus)
            pa.node = r[pre.alias]
            a._discourse = pa
        elif isinstance(pre, SpeakerAnnotation):
            pa = Speaker(corpus)
            pa.node = r[pre.alias]
            a._speaker = pa

        elif isinstance(pre, HierarchicalAnnotation):
            pa = LinguisticAnnotation(corpus)
            pa.node = r[pre.alias]
            pa.type_node = r[pre.type_alias]

            a._supers[pre.node_type] = pa
        elif isinstance(pre, QuerySubAnnotation):
            subannotations = r[pre.collection_alias]
            for s in subannotations:
                sa = SubAnnotation(corpus)
                sa._annotation = a
                sa.node = s
                if sa._type not in a._subannotations:
                    a._subannotations[sa._type] = []
                a._subannotations[sa._type].append(sa)
        elif isinstance(pre, SubPathAnnotation):
            subs = r[pre.collection_alias]
            sub_types = r[pre.collection_type_alias]
            subbed = []
            subannotations = r[pre.subannotation_alias]
            for i, e in enumerate(subs):
                pa = LinguisticAnnotation(corpus)
                pa.node = e
                pa.type_node = sub_types[i]
                pa._preloaded = True
                for s in subannotations[i]:
                    sa = SubAnnotation(corpus)
                    sa._annotation = pa
                    sa.node = s
                    if sa._type not in pa._subannotations:
                        pa._subannotations[sa._type] = []
                    pa._subannotations[sa._type].append(sa)
                subbed.append(pa)
            a._subs[pre.collected_node.node_type] = subbed
    return a


class QueryResults(BaseQueryResults):
    def __init__(self, query):
        super(QueryResults, self).__init__(query)
        self.speaker_discourse_channels = {}
        self.num_tracks = 0
        self.track_columns = set()
        if query._columns:
            self._acoustic_columns = query._acoustic_columns
            for x in query._acoustic_columns:
                if isinstance(x, Track):
                    self.num_tracks += 1
                    self.track_columns.update(x.output_columns)
                self.columns.extend(x.output_columns)
        if query._columns and self._acoustic_columns:
            statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
            RETURN s.name as speaker, d.name as discourse, r.channel as channel'''.format(corpus_name=self.corpus.cypher_safe_name)
            results = self.corpus.execute_cypher(statement)
            for r in results:
                self.speaker_discourse_channels[r['speaker'], r['discourse']] = r['channel']

    def _sanitize_record(self, r):
        if self.models:
            r = hydrate_model(r, self._to_find, self._to_find_type, self._preload, self.corpus)
        else:
            r = AnnotationRecord(r)
            cache = {}
            for a in self._acoustic_columns:
                if a.attribute is not None and a.attribute.label in cache:
                    a.attribute.cached_settings, a.attribute.cached_data = cache[a.attribute.label]
                elif a.label in cache:
                    a.cached_settings, a.cached_data = cache[a.label]
                if r[a.begin_alias] is None:
                    for k in a.output_columns:
                        r.add_acoustic(k, None)
                else:
                    discourse = r[a.discourse_alias]
                    speaker = r[a.speaker_alias]
                    channel = self.speaker_discourse_channels[speaker, discourse]
                    t = a.hydrate(self.corpus, discourse,
                                  r[a.begin_alias],
                                  r[a.end_alias],
                                  channel)
                    if a.attribute is not None and a.attribute.label not in cache:
                        cache[a.attribute.label] = a.attribute.cached_settings, a.attribute.cached_data
                    elif a.label in cache:
                        cache[a.label] = a.cached_settings, a.cached_data
                    for k in a.output_columns:
                        if k == 'time':
                            continue
                        if k in self.track_columns:
                            r.add_track(t)
                        else:
                            r.add_acoustic(k, t[k])
        return r

    def rows_for_csv(self):
        header = self.columns
        for line in self:
            baseline = {k: line[k] for k in header if k not in self.track_columns}
            if line.track:
                for k, v in sorted(line.track.items()):
                    line = {}
                    line.update(baseline)
                    line.update({'time': k})
                    line.update(v)
                    yield line
            else:
                yield baseline

    def to_csv(self, path, mode='w'):
        if self.num_tracks > 1:
            raise (GraphQueryError('Only one track attribute can currently be exported to csv.'))
        super(QueryResults, self).to_csv(path, mode=mode)


class AnnotationRecord(BaseRecord):
    def __init__(self, result):
        self.columns = result.keys()
        self.values = result.values()
        self.acoustic_columns = []
        self.acoustic_values = []
        self.track = {}
        self.track_columns = []

    def __getitem__(self, key):
        if key in self.columns:
            return self.values[self.columns.index(key)]
        elif key in self.acoustic_columns:
            return self.acoustic_values[self.acoustic_columns.index(key)]
        raise KeyError('{} not in columns {} or {}'.format(key, self.columns, self.acoustic_columns))

    def add_acoustic(self, key, value):
        self.acoustic_columns.append(key)
        self.acoustic_values.append(value)

    def add_track(self, track):
        # Could use interpolation of tracks?
        columns = set(self.track_columns)
        for k, v in track.items():
            if k not in self.track:
                self.track[k] = v
            else:
                self.track[k].update(v)
            columns.update(v.keys())
        self.track_columns = sorted(columns)
