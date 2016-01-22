
from uuid import uuid1
import hashlib

from ..helper import normalize_values_for_neo4j

class PGAnnotation(object):
    def __init__(self, label, begin, end):
        self.id = uuid1()
        self.label = label
        self.begin = begin
        self.end = end
        try:
            self.midpoint = (self.end - self.begin) / 2 + self.begin
        except TypeError:
            self.midpoint = None

        self.type_properties = {}
        self.token_properties = {}
        self.super_id = None
        self.previous_id = None
        self.speaker = None

        self.subannotations = []

    def sha(self):
        m = hashlib.sha1()
        m.update(' '.join(map(str, self.type_values())).encode())
        return m.hexdigest()

    def type_keys(self):
        keys = list(self.type_properties.keys())
        if self.label is not None:
            keys.append('label')
        return sorted(keys)

    def type_values(self):
        normalized = normalize_values_for_neo4j(self.type_properties)
        for k in self.type_keys():
            if k == 'label':
                yield self.label
            else:
                yield normalized[k]

    def token_keys(self):
        keys = list(self.token_properties.keys())
        if self.label is not None:
            keys.append('label')
        return sorted(keys)

    def token_values(self):
        normalized = normalize_values_for_neo4j(self.token_properties)
        for k in self.token_keys():
            if k == 'label':
                yield self.label
            else:
                yield normalized[k]


class PGAnnotationType(object):
    def __init__(self, name):
        self.name = name
        self._list = []
        self.supertype = None
        self.type_property_keys = set()
        self.token_property_keys = set()
        self.is_word = False

    def add(self, annotation):
        self._list.append(annotation)
        self.type_property_keys.update(annotation.type_keys())
        self.token_property_keys.update(annotation.token_keys())

    @property
    def speakers(self):
        speakers = set()
        for x in self:
            if x.speaker is None:
                continue
            speakers.add(x.speaker)
        return speakers

    def lookup(self, timepoint, speaker = None):
        if speaker is None:
            return next((x for x in self._list
                            if timepoint >= x.begin and
                                timepoint <= x.end),
                        None)
        else:
            return next((x for x in self._list
                            if x.speaker == speaker and
                                timepoint >= x.begin and
                                timepoint <= x.end),
                        None)

    def lookup_range(self, begin, end, speaker = None):
        if speaker is None:
            return sorted([x for x in self._list
                            if x.midpoint >= begin and
                                x.midpoint <= end],
                        key = lambda x: x.begin)
        else:
            return sorted([x for x in self._list
                            if x.speaker == speaker and
                                x.midpoint >= begin and
                                x.midpoint <= end],
                        key = lambda x: x.begin)

    def __getitem__(self, key):
        return self._list[key]

    def __iter__(self):
        for a in self._list:
            yield a

class PGSubAnnotation(PGAnnotation):
    def __init__(self, label, type, begin, end):
        self.id = uuid1()
        self.label = label
        self.type = type
        self.begin = begin
        self.end = end

        self.type_properties = {}
        self.token_properties = {}

