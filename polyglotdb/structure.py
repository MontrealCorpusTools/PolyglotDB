

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

    get_lower_types = contains
    get_higher_types = contained_by

    def add_subannotation_type(self, linguistic_type, subannotation_type):
        if linguistic_type not in self.subannotations:
            self.subannotations[linguistic_type] = set()
        self.subannotations[linguistic_type].add(subannotation_type)
