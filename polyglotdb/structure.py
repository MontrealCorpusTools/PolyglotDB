
from .graph.helper import value_for_cypher

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
    def __init__(self, data = None):
        if data is None:
            data = {}
        self._data = data
        self.subannotations = {}
        self.annotation_types = set(data.keys())
        self.subset_types = {}
        self.token_properties = {}
        self.subset_tokens = {}
        self.type_properties = {}


    def add_type_labels(self, corpus_context, annotation_type, labels):
        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        RETURN n'''.format(type = annotation_type)
        res = corpus_context.execute_cypher(statement, corpus_name = corpus_context.corpus_name)
        try:
            cur_subsets = res[0].n.subsets
        except AttributeError:
            cur_subsets = []
        updated = set(cur_subsets + labels)
        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        SET n.subsets = {{subsets}}'''.format(type = annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                corpus_name = corpus_context.corpus_name)

    def add_token_labels(self, corpus_context, annotation_type, labels):
        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n:{type})
        RETURN n'''.format(type = annotation_type)
        res = corpus_context.execute_cypher(statement, corpus_name = corpus_context.corpus_name)
        try:
            cur_subsets = res[0].n.subsets
        except AttributeError:
            cur_subsets = []
        updated = set(cur_subsets + labels)
        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(n:{type})
        SET n.subsets = {{subsets}}'''.format(type = annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                corpus_name = corpus_context.corpus_name)

    def add_type_properties(self, corpus_context, annotation_type, properties):
        set_template = 'n.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k,v in properties:
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
            ps.append(set_template.format(k))
            kwargs[k] = v

        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        SET {sets}'''.format(type = annotation_type, sets = ', '.join(ps))
        corpus_context.execute_cypher(statement,
                corpus_name = corpus_context.corpus_name, **kwargs)

        if annotation_type not in self.type_properties:
            self.type_properties[annotation_type] = set([('id',str)])
        self.type_properties[annotation_type].update(k for k in properties)

    def add_token_properties(self, corpus_context, annotation_type, properties):
        set_template = 'n.{0} = {{{0}}}'
        ps = []
        kwargs = {}
        for k,v in properties:
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
        SET {sets}'''.format(type = annotation_type, sets = ', '.join(ps))
        corpus_context.execute_cypher(statement,
                corpus_name = corpus_context.corpus_name, **kwargs)
        if annotation_type not in self.token_properties:
            self.token_properties[annotation_type] = set([('id', str)])
        self.token_properties[annotation_type].update(k for k in properties)

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
        self.annotation_types.add(key)

    def __delitem__(self, key):
        del self._data[key]
        for k,v in self._data.items():
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
            for k,v in other.type_properties.items():
                if k not in self.type_properties.items():
                    self.type_properties[k] = v
                else:
                    self.type_properties[k] = self.type_properties[k] & v
                if k not in self.token_properties.items():
                    self.token_properties[k] = other.token_properties[k]
                else:
                    self.type_properties[k] = self.type_properties[k] & other.token_properties[k]
        self.annotation_types.update(self._data.keys())

    @property
    def lowest(self):
        for k in self.keys():
            if k not in self.values():
                return k

    @property
    def highest(self):
        for k,v in self.items():
            if v is None:
                return k

    @property
    def highest_to_lowest(self):
        ats = [self.highest]
        while len(ats) < len(self.keys()):
            for k,v in self.items():
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
        if linguistic_type not in self.subannotations:
            self.subannotations[linguistic_type] = set()
        self.subannotations[linguistic_type].add(subannotation_type)

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
