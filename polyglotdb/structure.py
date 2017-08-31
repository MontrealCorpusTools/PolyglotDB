from .exceptions import HierarchyError, GraphQueryError
from .query.annotations.attributes import PauseAnnotation, AnnotationNode


class Hierarchy(object):
    '''
    Class containing information about how a corpus is structured.

    Hierarchical data is stored in the form of a dictionary with keys
    for linguistic types, and values for the linguistic type that contains
    them.  If no other type contains a given type, its value is ``None``.

    Subannotation data is stored in the form of a dictionary with keys
    for linguistic types, and values of sets of types of subannotations.

    Parameters
    ----------
    data : dict
        Information about the hierarchy of linguistic types
    subannotations : dict
        Information about what subannotations a linguistic type contains
    '''

    get_type_subset_template = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        RETURN n.subsets as subsets'''
    set_type_subset_template = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        SET n.subsets = {{subsets}}'''

    get_token_subset_template = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n:{type})
        RETURN n.subsets as subsets'''
    set_token_subset_template = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n:{type})
        SET n.subsets = {{subsets}}'''

    def __init__(self, data=None, corpus_name=None):
        if data is None:
            data = {}
        self._data = data
        self.corpus_name = corpus_name
        self.subannotations = {}
        self.subannotation_properties = {}
        self.subset_types = {}
        self.token_properties = {}
        self.subset_tokens = {}
        self.type_properties = {}

        self.speaker_properties = {('name', str)}
        self.discourse_properties = {('name', str), ('file_path', str), ('low_freq_file_path', str), ('vowel_file_path', str), ('consonant_file_path', str), ('duration', float), ('sampling_rate', int), ('num_channels', int)}

    def __getattr__(self, key):
        if key == 'pause':
            return PauseAnnotation(corpus=self.corpus_name)
        if key + 's' in self.annotation_types:
            key += 's'  # FIXME
        if key in self.annotation_types:
            return AnnotationNode(key, corpus=self.corpus_name, hierarchy=self)
        raise (GraphQueryError(
            'The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(key, ', '.join(
                sorted(self.annotation_types)))))

    def __getstate__(self):
        return self.to_json()

    def __setstate__(self, state):
        self.from_json(state)

    def get_depth(self, lower_type, higher_type):
        depth = 1
        t = self.get_higher_types(lower_type)
        for i in t:
            if i == higher_type:
                break
            depth += 1
        return depth

    @property
    def annotation_types(self):
        return set(self._data.keys())

    def to_json(self):
        data = {'_data': self._data}
        data['corpus_name'] = self.corpus_name
        data['subannotations'] = {k: sorted(v) for k, v in self.subannotations.items()}
        data['subannotation_properties'] = {k: sorted((name, t()) for name, t in v) for k, v in
                                            self.subannotation_properties.items()}
        data['subset_types'] = {k: sorted(v) for k, v in self.subset_types.items()}
        data['subset_tokens'] = {k: sorted(v) for k, v in self.subset_tokens.items()}
        data['token_properties'] = {k: sorted((name, t()) for name, t in v) for k, v in self.token_properties.items()}
        data['type_properties'] = {k: sorted((name, t()) for name, t in v) for k, v in self.type_properties.items()}
        data['speaker_properties'] = sorted((name, t()) for name, t in self.speaker_properties)
        data['discourse_properties'] = sorted((name, t()) for name, t in self.discourse_properties)
        return data

    def from_json(self, json):
        self._data = json['_data']
        self.corpus_name = json['corpus_name']
        self.subannotations = {k: set(v) for k, v in json['subannotations'].items()}
        self.subannotation_properties = {k: set((name, type(t)) for name, t in v) for k, v in
                                         json['subannotation_properties'].items()}
        self.subset_types = {k: set(v) for k, v in json['subset_types'].items()}
        self.subset_tokens = {k: set(v) for k, v in json['subset_tokens'].items()}
        self.token_properties = {k: set((name, type(t)) for name, t in v) for k, v in json['token_properties'].items()}
        self.type_properties = {k: set((name, type(t)) for name, t in v) for k, v in json['type_properties'].items()}
        self.speaker_properties = set((name, type(t)) for name, t in json['speaker_properties'])
        self.discourse_properties = set((name, type(t)) for name, t in json['discourse_properties'])

    def add_type_labels(self, corpus_context, annotation_type, labels):
        statement = self.get_type_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets + labels)
        statement = self.set_type_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_types[annotation_type] = updated

    def remove_type_labels(self, corpus_context, annotation_type, labels):
        statement = self.get_type_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets) - set(labels)
        statement = self.set_type_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_types[annotation_type] = updated

    def add_token_labels(self, corpus_context, annotation_type, labels):
        statement = self.get_token_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets + labels)
        statement = self.set_token_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_tokens[annotation_type] = updated

    def remove_token_labels(self, corpus_context, annotation_type, labels):
        statement = self.get_token_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets) - set(labels)
        statement = self.set_token_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_tokens[annotation_type] = updated

    def add_annotation_type(self, annotation_type, above=None, below=None):
        self._data[above] = annotation_type
        self._data[annotation_type] = below
        self.token_properties[annotation_type] = {('label', str), ('begin', float), ('end', float)}
        self.type_properties[annotation_type] = {('label', str)}

    def remove_annotation_type(self, annotation_type):
        cur_above = self._data[annotation_type]
        cur_below = [k for k, v in self._data.items() if v == annotation_type][0]
        del self._data[annotation_type]
        self._data[cur_below] = cur_above
        try:
            del self.token_properties[annotation_type]
        except KeyError:
            pass
        try:
            del self.type_properties[annotation_type]
        except KeyError:
            pass
        try:
            del self.subset_types[annotation_type]
        except KeyError:
            pass
        try:
            del self.subset_tokens[annotation_type]
        except KeyError:
            pass
        if annotation_type in self.subannotations:
            for s in self.subannotations[annotation_type]:
                del self.subannotation_properties[s]
            del self.subannotations

    def add_type_properties(self, corpus_context, annotation_type, properties):
        set_template = 'n.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k, v in properties:
            if v == int:
                v = 0
            elif v == list:
                v = []
            elif v == float:
                v = 0.0
            elif v == str:
                v = ''
            elif v == bool:
                v = False
            elif v == type(None):
                v = None
            ps.append(set_template.format(k))
            kwargs[k] = v

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        SET {sets}'''.format(type=annotation_type, sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        if annotation_type not in self.type_properties:
            self.type_properties[annotation_type] = {('id', str)}
        self.type_properties[annotation_type].update(k for k in properties)

    def remove_type_properties(self, corpus_context, annotation_type, properties):
        remove_template = 'n.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        REMOVE {removes}'''.format(type=annotation_type, removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        if annotation_type not in self.type_properties:
            self.type_properties[annotation_type] = {('id', str)}

        to_remove = set(x for x in self.type_properties[annotation_type] if x[0] in properties)
        self.type_properties[annotation_type].difference_update(to_remove)

    def add_token_properties(self, corpus_context, annotation_type, properties):
        set_template = 'n.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k, v in properties:
            if v == int:
                v = 0
            elif v == list:
                v = []
            elif v == float:
                v = 0.0
            elif v == str:
                v = ''
            elif v == bool:
                v = False
            elif v == type(None):
                v = None
            ps.append(set_template.format(k))
            kwargs[k] = v

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n:{type})
        SET {sets}'''.format(type=annotation_type, sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)
        if annotation_type not in self.token_properties:
            self.token_properties[annotation_type] = {('id', str)}
        self.token_properties[annotation_type].update(k for k in properties)

    def remove_token_properties(self, corpus_context, annotation_type, properties):
        remove_template = 'n.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n:{type})
        REMOVE {removes}'''.format(type=annotation_type, removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        if annotation_type not in self.token_properties:
            self.token_properties[annotation_type] = {('id', str)}
        to_remove = set(x for x in self.token_properties[annotation_type] if x[0] in properties)
        self.token_properties[annotation_type].difference_update(to_remove)

    def add_speaker_properties(self, corpus_context, properties):
        set_template = 's.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k, v in properties:
            if v == int:
                v = 0
            elif v == list:
                v = []
            elif v == float:
                v = 0.0
            elif v == str:
                v = ''
            elif v == bool:
                v = False
            elif v == type(None):
                v = None
            ps.append(set_template.format(k))
            kwargs[k] = v

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)-[:spoken_by]->(s:Speaker)
        SET {sets}'''.format(sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        self.speaker_properties.update(k for k in properties)

    def remove_speaker_properties(self, corpus_context, properties):
        remove_template = 's.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)-[:spoken_by]->(s:Speaker)
        REMOVE {removes}'''.format(removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        to_remove = set(x for x in self.speaker_properties if x[0] in properties)
        self.speaker_properties.difference_update(to_remove)

    def add_discourse_properties(self, corpus_context, properties):
        set_template = 'd.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k, v in properties:
            if v == int:
                v = 0
            elif v == list:
                v = []
            elif v == float:
                v = 0.0
            elif v == str:
                v = ''
            elif v == bool:
                v = False
            elif v == type(None):
                v = None
            ps.append(set_template.format(k))
            kwargs[k] = v

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)-[:spoken_in]->(d:Discourse)
        SET {sets}'''.format(sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        self.discourse_properties.update(k for k in properties)

    def remove_discourse_properties(self, corpus_context, properties):
        remove_template = 'd.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)-[:spoken_in]->(d:Discourse)
        REMOVE {removes}'''.format(removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        to_remove = set(x for x in self.discourse_properties if x[0] in properties)
        self.discourse_properties.difference_update(to_remove)

    def keys(self):
        '''
        Keys (linguistic types) of the hierarchy.

        Returns
        -------
        generator
            Keys of the hierarchy
        '''
        return self._data.keys()

    def values(self):
        '''
        Values (containing types) of the hierarchy.

        Returns
        -------
        generator
            Values of the hierarchy
        '''
        return self._data.values()

    def items(self):
        '''
        Key/value pairs for the hierarchy.

        Returns
        -------
        generator
            Items of the hierarchy
        '''
        return self._data.items()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]
        for k, v in self._data.items():
            if v == key:
                self._data[k] = None

    def __contains__(self, item):
        return item in self._data

    def update(self, other):
        '''
        Merge Hierarchies together.  If other is a dictionary, then only
        the hierarchical data is updated.

        Parameters
        ----------
        other : Hierarchy or dict
            Data to be merged in
        '''
        if isinstance(other, dict):
            self._data.update(other)
        else:
            self._data.update(other._data)
            self.subannotations.update(other.subannotations)
            self.subannotation_properties.update(other.subannotation_properties)
            for k, v in other.subannotation_properties.items():
                if k not in self.subannotation_properties:
                    self.subannotation_properties[k] = v
                else:
                    self.subannotation_properties[k] = self.subannotation_properties[k] & v
            for k, v in other.type_properties.items():
                if k not in self.type_properties.items():
                    self.type_properties[k] = v
                else:
                    self.type_properties[k] = self.type_properties[k] & v
            for k, v in other.token_properties.items():
                if k not in self.token_properties.items():
                    self.token_properties[k] = other.token_properties[k]
                else:
                    self.token_properties[k] = self.token_properties[k] & other.token_properties[k]

    @property
    def lowest(self):
        for k in self.keys():
            if k not in self.values():
                return k

    @property
    def highest(self):
        for k, v in self.items():
            if v is None:
                return k

    @property
    def highest_to_lowest(self):
        ats = [self.highest]
        while len(ats) < len(self.keys()):
            for k, v in self.items():
                if v == ats[-1]:
                    ats.append(k)
                    break
        return ats

    @property
    def lowest_to_highest(self):
        ats = [self.lowest]
        while len(ats) < len(self.keys()):
            ats.append(self[ats[-1]])
        return ats

    def contained_by(self, key):
        supertype = self[key]
        supertypes = [supertype]
        if supertype is not None:
            while True:
                supertype = self[supertype]
                if supertype is None:
                    break
                supertypes.append(supertype)
        return supertypes

    def contains(self, key):
        supertypes = self.contained_by(key)

        return [x for x in sorted(self.keys()) if x not in supertypes and x != key]

    def get_lower_types(self, key):
        lower = []
        found = False
        for t in self.highest_to_lowest:
            if t == key:
                found = True
                continue
            if found:
                lower.append(t)
        return lower

    def get_higher_types(self, key):
        higher = []
        found = False
        for t in self.lowest_to_highest:
            if t == key:
                found = True
                continue
            if found:
                higher.append(t)
        return higher

    def add_subannotation_type(self, linguistic_type, subannotation_type):
        if subannotation_type in self.subannotation_properties:
            raise (HierarchyError('The subannotation_type {} is already specified for another linguistic type.'
                                  ' Please use a different name.'.format(subannotation_type)))
        if linguistic_type not in self.subannotations:
            self.subannotations[linguistic_type] = set()
        self.subannotations[linguistic_type].add(subannotation_type)
        self.subannotation_properties[subannotation_type] = set()

    def remove_subannotation_type(self, subannotation_type):
        try:
            del self.subannotation_properties[subannotation_type]
        except KeyError:
            pass
        for k, v in self.subannotations.items():
            if subannotation_type in v:
                self.subannotations[k] = v - {subannotation_type}

    def add_subannotation_properties(self, corpus_context, subannotation_type, properties):
        set_template = 'n.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k, v in properties:
            if v == int:
                v = 0
            elif v == list:
                v = []
            elif v == float:
                v = 0.0
            elif v == str:
                v = ''
            elif v == bool:
                v = False
            elif v == type(None):
                v = None
            ps.append(set_template.format(k))
            kwargs[k] = v

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n)<-[:annotates]-(n:{type})
        SET {sets}'''.format(sets=', '.join(ps), type=subannotation_type)
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        self.subannotation_properties[subannotation_type].update(k for k in properties)

    def has_speaker_property(self, key):
        for name, t in self.speaker_properties:
            if name == key:
                return True
        return False

    def has_discourse_property(self, key):
        for name, t in self.discourse_properties:
            if name == key:
                return True
        return False

    def has_token_property(self, type, key):
        if type not in self.token_properties:
            return False
        for name, t in self.token_properties[type]:
            if name == key:
                return True
        return False

    def has_type_property(self, type, key):
        if type not in self.type_properties:
            return False
        for name, t in self.type_properties[type]:
            if name == key:
                return True
        return False

    def has_type_subset(self, type, key):
        if type not in self.subset_types:
            return False
        for name in self.subset_types[type]:
            if name == key:
                return True
        return False

    def has_token_subset(self, type, key):
        if type not in self.subset_tokens:
            return False
        for name in self.subset_tokens[type]:
            if name == key:
                return True
        return False

    @property
    def word_name(self):
        for at in self.annotation_types:
            if at.startswith('word'):
                return at
        return None

    @property
    def phone_name(self):
        return self.lowest
