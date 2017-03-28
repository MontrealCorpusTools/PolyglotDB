from uuid import uuid1
import hashlib

from ..helper import normalize_values_for_neo4j


class PGAnnotation(object):
    def __init__(self, label, begin, end):
        self.id = uuid1()
        self.label = label
        if begin > end:
            begin, end = end, begin
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

    def sha(self, corpus=None):
        """
        Constructs hash of values and corpus name

        Parameters
        ----------
        corpus : str
            defaults to None
        Returns
        -------
        str
            a hex string containing the digest of the values as hexadecimal numbers
        """
        m = hashlib.sha1()
        value = ' '.join(map(str, self.type_values()))
        if corpus is not None:
            value += ' ' + corpus
        m.update(value.encode())
        out = m.hexdigest()
        return out

    def type_keys(self):
        """
        adds label to type property keys and sorts them

        Returns
        -------
        list 
            sorted list of property keys
        """
        keys = list(self.type_properties.keys())
        if self.label is not None:
            keys.append('label')
        return sorted(keys)

    def type_values(self):
        """
        Normalizes type properties for neo4j, yields label or property

        Yields
        ------
        str
            either the property label or the property if there is no label
        

        """
        normalized = normalize_values_for_neo4j(self.type_properties)
        for k in self.type_keys():
            if k == 'label':
                yield self.label
            else:
                yield normalized[k]

    def token_keys(self):
        """
        adds label to token property keys and sorts them

        Returns
        -------
        list 
            sorted list of property keys
        """
        keys = list(self.token_properties.keys())
        if self.label is not None:
            keys.append('label')
        return sorted(keys)

    def token_values(self):
        """
        Normalizes token properties for neo4j, yields label or property

        Yields
        ------
        str
            either the property label or the property if there is no label
        

        """
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
        self.type_properties = set()
        self.token_properties = set()
        self.is_word = False
        self._lookup_dict = None

    def optimize_lookups(self):
        """
        optimizes the lookup dictionary
        """
        if self._lookup_dict is not None:
            return
        self._list = sorted(self._list, key=lambda x: x.begin)
        if len(self._list) > 1000:
            self._lookup_dict = {}
            cur = 0
            while cur < len(self._list):
                self._lookup_dict[cur] = self._list[cur].begin
                cur += 1000

    def add(self, annotation):
        """
        adds annotation to PGAnnotationType object

        Parameters
        ----------
        annotation :class: `~polyglotdb.io.types.BaseAnnotation`
            the annotation to add
        """
        self._list.append(annotation)
        self.type_property_keys.update(annotation.type_keys())
        for k, v in annotation.type_properties.items():
            if isinstance(v, list):
                t = str
            else:
                t = type(v)
            self.type_properties.add((k, t))
        self.token_property_keys.update(annotation.token_keys())
        self.token_properties.update((k, type(v)) for k, v in annotation.token_properties.items() if v is not None)

    @property
    def speakers(self):
        """
        Gets the speakers from a PGAnnotationType object

        Returns
        -------
        speakers : set
            a set of speakers
        """
        speakers = set()
        for x in self:
            s = 'unknown'
            if x.speaker is not None:
                s = x.speaker
            speakers.add(s)
        return speakers

    def lookup(self, timepoint, speaker=None):
        """
        Searches the lookup_dict for a particular begin time, and optionally a speaker 

        Parameters
        ----------
        timepoint : double
            the begin of the desired linguistic object
        speaker : str
            Defaults to None
        """
        if self._lookup_dict is not None:
            prev = 0
            for ind, time in sorted(self._lookup_dict.items()):
                if timepoint < time:
                    if prev != 0:
                        prev -= 500
                    lookup_list = self._list[prev:ind + 100]
                    break
                prev = ind
            else:
                if ind != 0:
                    ind -= 500
                lookup_list = self._list[ind:]
        else:
            lookup_list = self._list
        if speaker is None:
            return next((x for x in lookup_list
                         if timepoint >= x.begin and
                         timepoint <= x.end),
                        None)
        else:
            return next((x for x in lookup_list
                         if x.speaker == speaker and
                         timepoint >= x.begin and
                         timepoint <= x.end),
                        None)

    def lookup_range(self, begin, end, speaker=None):
        """
        Searches the lookup_dict for objects between begin time, end time, and optionally a speaker 

        Parameters
        ----------
        begin : double
            the lower bound of the range
        end : double
            the upper bound of the range
        speaker : str
            Defaults to None
        """
        if self._lookup_dict is not None:
            prev = 0
            mapping = sorted(self._lookup_dict.items())
            for i, (ind, time) in enumerate(mapping):
                if begin < time:
                    if end < time:
                        lookup_list = self._list[prev:ind]
                    else:
                        try:
                            lookup_list = self._list[prev:mapping[i + 1][0]]
                        except IndexError:
                            lookup_list = self._list[prev:]
                    break
                prev = ind
            else:
                lookup_list = self._list[ind:]
        else:
            lookup_list = self._list
        if speaker is None:
            return sorted([x for x in lookup_list
                           if x.midpoint >= begin and
                           x.midpoint <= end],
                          key=lambda x: x.begin)
        else:
            return sorted([x for x in lookup_list
                           if x.speaker == speaker and
                           x.midpoint >= begin and
                           x.midpoint <= end],
                          key=lambda x: x.begin)

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
