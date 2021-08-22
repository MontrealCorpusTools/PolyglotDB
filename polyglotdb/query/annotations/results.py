
from polyglotdb.exceptions import GraphQueryError

from ..base.results import BaseQueryResults, BaseRecord

from .attributes import (HierarchicalAnnotation, SubPathAnnotation,
                         SubAnnotation as QuerySubAnnotation,
                         SpeakerAnnotation, DiscourseAnnotation,
                         Track as TrackAnnotation)
from .attributes.precedence import FollowingAnnotation, PreviousAnnotation
from ...acoustics.classes import Track
from .models import LinguisticAnnotation, SubAnnotation, Speaker, Discourse


def hydrate_model(r, to_find, to_find_type, to_preload, to_preload_acoustics, corpus):
    base_annotation_type = to_find.replace('node_', '')
    a = LinguisticAnnotation(corpus)
    r[to_find]['neo4j_label'] = to_find.replace('node_', '')
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

    for pre in to_preload:
        if isinstance(pre, HierarchicalAnnotation):
            pa = LinguisticAnnotation(corpus)
            r[pre.alias]['neo4j_label'] = pre.alias.split('_')[-1]
            pa.node = r[pre.alias]
            pa.type_node = r[pre.type_alias]
            pa._preloaded = True
            pa._discourse = a._discourse
            pa._speaker = a._speaker
            a._supers[pre.node_type] = pa
        elif isinstance(pre, QuerySubAnnotation):
            subannotations = r[pre.collection_alias]
            for s in subannotations:
                sa = SubAnnotation(corpus)
                s['neo4j_label'] = pre.collection_alias.split('_in_')[0].replace('node_', '')
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
                e['neo4j_label'] = pre.collected_node.alias.replace('node_', '')
                pa.node = e
                pa.type_node = sub_types[i]
                pa._preloaded = True
                for s in subannotations[i]:
                    sa = SubAnnotation(corpus)
                    sa._annotation = pa
                    s['neo4j_label'] = pre.subannotation_alias.split('_in_')[0].replace('node_', '')
                    sa.node = s
                    if sa._type not in pa._subannotations:
                        pa._subannotations[sa._type] = []
                    pa._subannotations[sa._type].append(sa)
                subbed.append(pa)
            a._subs[pre.collected_node.node_type] = subbed

    follows = sorted([x for x in to_preload if isinstance(x, FollowingAnnotation) and x.node_type == base_annotation_type],
                     key=lambda x: x.pos)
    current = a
    for pre in follows:
        if r[pre.alias] is None:
            current._following = 'empty'
            break
        pa = LinguisticAnnotation(corpus)
        pa._preloaded = True
        pa = LinguisticAnnotation(corpus)
        r[pre.alias]['neo4j_label'] = pre.alias.split('_')[-1]
        pa.node = r[pre.alias]
        pa.type_node = r[pre.type_alias]
        pa._discourse = a._discourse
        pa._speaker = a._speaker
        current._following = pa
        current = pa

    prevs = sorted([x for x in to_preload if isinstance(x, PreviousAnnotation) and x.node_type == base_annotation_type], key=lambda x: x.pos, reverse=True)
    current = a
    for pre in prevs:
        if r[pre.alias] is None:
            current._previous = 'empty'
            break
        pa = LinguisticAnnotation(corpus)
        pa._preloaded = True
        r[pre.alias]['neo4j_label'] = pre.alias.split('_')[-1]
        pa.node = r[pre.alias]
        pa.type_node = r[pre.type_alias]
        pa._discourse = a._discourse
        pa._speaker = a._speaker
        current._previous = pa
        current = pa

    for k, v in a._supers.items():
        follows = sorted([x for x in to_preload if isinstance(x, FollowingAnnotation) and x.node_type == k],
                         key=lambda x: x.pos)
        current = v
        for pre in follows:
            if r[pre.alias] is None:
                current._following = 'empty'
                break
            pa = LinguisticAnnotation(corpus)
            pa._preloaded = True
            pa = LinguisticAnnotation(corpus)
            r[pre.alias]['neo4j_label'] = pre.alias.split('_')[-1]
            pa.node = r[pre.alias]
            pa.type_node = r[pre.type_alias]
            pa._discourse = a._discourse
            pa._speaker = a._speaker
            current._following = pa
            current = pa

        prevs = sorted([x for x in to_preload if isinstance(x, PreviousAnnotation) and x.node_type == k], key=lambda x: x.pos, reverse=True)
        current = v
        for pre in prevs:
            if r[pre.alias] is None:
                current._previous = 'empty'
                break
            pa = LinguisticAnnotation(corpus)
            pa._preloaded = True
            r[pre.alias]['neo4j_label'] = pre.alias.split('_')[-1]
            pa.node = r[pre.alias]
            pa.type_node = r[pre.type_alias]
            pa._discourse = a._discourse
            pa._speaker = a._speaker
            current._previous = pa
            current = pa

    for pre in to_preload_acoustics:
        if a._type == 'utterance':
            utterance_id = a.id
        else:
            utterance_id = a.utterance.id
        if utterance_id not in pre.attribute.cache:
            data = corpus.get_utterance_acoustics(pre.attribute.label, utterance_id, a.discourse.name, a.speaker.name)
            pre.attribute.cache[utterance_id] = data
        a._load_track(pre)
    return a


class QueryResults(BaseQueryResults):
    def __init__(self, query):
        super(QueryResults, self).__init__(query)
        self.speaker_discourse_channels = {}
        self.num_tracks = 0
        self.track_columns = []
        if query._columns:
            self._acoustic_columns = query._acoustic_columns
            for x in query._acoustic_columns:
                if isinstance(x, TrackAnnotation):
                    self.num_tracks += 1
                    self.track_columns.extend(y for y in x.output_columns if y not in self.track_columns)
                else:
                    self._columns.extend(x.output_columns)
        if query._columns and self._acoustic_columns:
            statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
            RETURN s.name as speaker, d.name as discourse, r.channel as channel'''.format(corpus_name=self.corpus.cypher_safe_name)
            results = self.corpus.execute_cypher(statement)
            for r in results:
                self.speaker_discourse_channels[r['speaker'], r['discourse']] = r['channel']
            self.acoustic_cache = {x: {} for x in sorted(query.corpus.hierarchy.acoustics)}
            for a in self._acoustic_columns:
                a.attribute.cache = self.acoustic_cache[a.attribute.label]
        if self.models:
            self._preload_acoustics = query._preload_acoustics
            if self._preload_acoustics:
                self.acoustic_cache = {x: {} for x in sorted(query.corpus.hierarchy.acoustics)}
                for a in self._preload_acoustics:
                    a.attribute.cache = self.acoustic_cache[a.attribute.label]


    @property
    def columns(self):
        return self._columns + self.track_columns

    def _sanitize_record(self, r):
        if self.models:
            r = hydrate_model(r, self._to_find, self._to_find_type, self._preload, self._preload_acoustics, self.corpus)
        else:
            r = AnnotationRecord(r)
            for a in self._acoustic_columns:
                if r[a.begin_alias] is None:
                    for k in a.output_columns:
                        r.add_acoustic(k, None)
                else:
                    utterance_id = r[a.utterance_alias]
                    discourse = r[a.discourse_alias]
                    speaker = r[a.speaker_alias]
                    if utterance_id not in a.attribute.cache:
                        data = self.corpus.get_utterance_acoustics(a.attribute.label, utterance_id, discourse, speaker)
                        a.attribute.cache[utterance_id] = data
                    t = a.hydrate(self.corpus, utterance_id,
                                  r[a.begin_alias],
                                  r[a.end_alias])
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
            if self.track_columns:
                for point in line.track:
                    line = {}
                    line.update(baseline)
                    line.update({'time': point.time})
                    line.update(point.select_values(self.track_columns))
                    yield line
            else:
                yield baseline

    def to_csv(self, path, mode='w'):
        if self.num_tracks > 1:
            raise (GraphQueryError('Only one track attribute can currently be exported to csv.'))
        super(QueryResults, self).to_csv(path, mode=mode)


class AnnotationRecord(BaseRecord):
    def __init__(self, result):
        self.columns = list(result.keys())
        self.values = list(result.values())
        self.acoustic_columns = []
        self.acoustic_values = []
        self.track = Track()
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

        for point in track:
            if point.time not in self.track:
                self.track.add(point)
            else:
                self.track[point.time].update(point)
        self.track_columns = self.track.keys()
