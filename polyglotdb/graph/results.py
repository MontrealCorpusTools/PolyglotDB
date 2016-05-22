

from polyglotdb.io import save_results

from .attributes import (HierarchicalAnnotation, SubPathAnnotation,
                            SubAnnotation as QuerySubAnnotation,
                            SpeakerAnnotation, DiscourseAnnotation)

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

            a._supers[pre.type] = pa
        elif isinstance(pre, QuerySubAnnotation):
            subannotations = r[pre.path_alias]
            for s in subannotations:
                sa = SubAnnotation(corpus)
                sa._annotation = a
                sa.node = s
                if sa._type not in a._subannotations:
                    a._subannotations[sa._type] = []
                a._subannotations[sa._type].append(sa)
        elif isinstance(pre, SubPathAnnotation):
            subs = r[pre.path_alias]
            sub_types = r[pre.path_type_alias]
            subbed = []
            subannotations = r[pre.subannotation_alias]
            for i,e in enumerate(subs):
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
            a._subs[pre.sub.type] = subbed
    return a

class QueryResults(object):
    def __init__(self, query):
        self.corpus = query.corpus
        self.cache = {}
        self.cursors = [self.corpus.execute_cypher(query.cypher(), **query.cypher_params())]
        self.evaluated = []
        self.current_cursor_ind = 0
        self.current_ind = 0
        if query._columns:
            self.models = False
            self._preload = None
            self._to_find = None
            self._to_find_type = None
            self._acoustic_columns = query._acoustic_columns
            self.columns = [x.output_alias for x in query._columns]
            self.columns.extend(x.output_alias for x in query._acoustic_columns)
        else:
            self.models = True
            self._preload = query._preload
            self._to_find = query.to_find.alias
            self._to_find_type = query.to_find.type_alias
            self.columns = None

    def __getitem__(self, key):
        cur = 0
        for i, c in enumerate(self.cursors):
            if i not in self.cache:
                self.cache[i] = []
            cur_cache_len = len(self.cache[i])
            if key < cur + cur_cache_len:
                return self.cache[i][key - cur]
            if i not in self.evaluated:
                self._cache_cursor(i, up_to = key - cur)
                cur_cache_len = len(self.cache[i])
                if key < cur + cur_cache_len:
                    return self.cache[i][key - cur]
            cur += cur_cache_len
        raise(IndexError(key))

    def _cache_cursor(self, i, up_to = None):
        while True:
            r = self.cursors[i].next()
            if r is None:
                self.evaluated.append(i)
                break
            r = self._sanitize_record(r)
            self.cache[i].append(r)
            if up_to is not None and len(self.cache[i]) > up_to:
                break

    def add_results(self, query):
        ## Add some validation
        cursor = self.corpus.execute_cypher(query.cypher(), **query.cypher_params())
        self.cursors.append(cursor)

    def next(self, number):
        pass

    def previous(self, number):
        pass

    def _sanitize_record(self, r):
        if self.models:
            r = hydrate_model(r, self._to_find, self._to_find_type, self._preload, self.corpus)
        else:
            print(r)
            r = Record(r)
            for a in self._acoustic_columns:
                t = a.hydrate(self.corpus, r[a.discourse_alias],
                            r[a.begin_alias],
                            r[a.end_alias])
                for k in a.output_columns:
                    r.add_acoustic(k, t[k])
        return r

    def __iter__(self):
        for i, c in enumerate(self.cursors):
            if i in self.cache:
                for r in self.cache[i]:
                    yield r
            else:
                self.cache[i] = []
            while True:
                r = c.next()
                if r is None:
                    self.evaluated.append(i)
                    break
                r = self._sanitize_record(r)
                self.cache[i].append(r)
                yield r

    def to_csv(self, path):
        save_results(self, path)

class Record(object):
    def __init__(self, result):
        self.columns = result.keys()
        self.values = result.values()
        self.acoustic_columns = []
        self.acoustic_values = []

    def __getitem__(self, key):
        if key in self.columns:
            return self.values[self.columns.index(key)]
        elif key in self.acoustic_columns:
            return self.acoustic_values[self.acoustic_columns.index(key)]
        raise KeyError(key)

    def add_acoustic(self, key, value):
        self.acoustic_columns.append(key)
        self.acoustic_values.append(value)
