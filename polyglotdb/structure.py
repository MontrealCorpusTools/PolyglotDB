from .exceptions import HierarchyError, GraphQueryError
from .query.annotations.attributes import PauseAnnotation, AnnotationNode
from datetime import datetime


class Hierarchy(object):
    """
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
    corpus_name : str
        Name of the corpus
    """

    get_type_subset_template = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        RETURN n.subsets as subsets"""
    set_type_subset_template = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        SET n.subsets = $subsets"""

    get_token_subset_template = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(n:{type})
        RETURN n.subsets as subsets"""
    set_token_subset_template = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(n:{type})
        SET n.subsets = $subsets"""

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
        self.acoustic_properties = {}

        self.speaker_properties = {('name', str)}
        self.discourse_properties = {('name', str), ('file_path', str), ('low_freq_file_path', str), ('vowel_file_path', str), ('consonant_file_path', str), ('duration', float), ('sampling_rate', int), ('num_channels', int)}

    def __getattr__(self, key):
        if key == 'pause':
            return PauseAnnotation(corpus=self.corpus_name, hierarchy=self)
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

    def __str__(self):
        return str(self.to_json())

    def get_depth(self, lower_type, higher_type):
        """
        Get the distance between two annotation types in the hierarchy

        Parameters
        ----------
        lower_type : str
            Name of the lower type
        higher_type : str
            Name of the higher type

        Returns
        -------
        int
            Distance between the two types
        """
        depth = 1
        t = self.get_higher_types(lower_type)
        for i in t:
            if i == higher_type:
                break
            depth += 1
        return depth

    @property
    def annotation_types(self):
        """
        Get a list of all the annotation types in the hierarchy

        Returns
        -------
        list
            All annotation types in the hierarchy

        """
        return list(self._data.keys())

    @property
    def acoustics(self):
        """
        Get all currently encoded acoustic measurements in the corpus

        Returns
        -------
        list
            All encoded acoustic measures
        """
        return sorted(self.acoustic_properties.keys())

    def to_json(self):
        """
        Convert the Hierarchy object to a dictionary for JSON serialization

        Returns
        -------
        dict
            All necessary information for the Hierarchy object
        """
        data = {'_data': self._data}
        data['corpus_name'] = self.corpus_name
        data['acoustic_properties'] = {k: sorted((name, t()) for name, t in v) for k, v in self.acoustic_properties.items()}
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
        """
        Set all properties from a dictionary deserialized from JSON

        Parameters
        ----------
        json : dict
            Object information
        """
        self._data = json['_data']
        self.corpus_name = json['corpus_name']
        self.acoustic_properties = {k: set((name, type(t)) for name, t in v) for k, v in json.get('acoustic_properties', {}).items()}
        self.subannotations = {k: set(v) for k, v in json['subannotations'].items()}
        self.subannotation_properties = {k: set((name, type(t)) for name, t in v) for k, v in
                                         json['subannotation_properties'].items()}
        self.subset_types = {k: set(v) for k, v in json['subset_types'].items()}
        self.subset_tokens = {k: set(v) for k, v in json['subset_tokens'].items()}
        self.token_properties = {k: set((name, type(t)) for name, t in v) for k, v in json['token_properties'].items()}
        self.type_properties = {k: set((name, type(t)) for name, t in v) for k, v in json['type_properties'].items()}
        self.speaker_properties = set((name, type(t)) for name, t in json['speaker_properties'])
        self.discourse_properties = set((name, type(t)) for name, t in json['discourse_properties'])

    def add_type_subsets(self, corpus_context, annotation_type, subsets):
        """
        Adds type subsets to the Hierarchy object for a corpus, and syncs it to the hierarchy schema in a Neo4j database

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type: str
            Annotation type to add subsets for
        subsets : iterable
            List of subsets to add for the annotation type
        """
        statement = self.get_type_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets + subsets)
        statement = self.set_type_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_types[annotation_type] = updated
        corpus_context.cache_hierarchy()

    def remove_type_subsets(self, corpus_context, annotation_type, subsets):
        """
        Removes type subsets to the Hierarchy object for a corpus, and syncs it to the hierarchy schema in a Neo4j database

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type: str
            Annotation type to remove subsets for
        subsets : iterable
            List of subsets to remove for the annotation type
        """
        statement = self.get_type_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets) - set(subsets)
        statement = self.set_type_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_types[annotation_type] = updated
        corpus_context.cache_hierarchy()

    def add_token_subsets(self, corpus_context, annotation_type, subsets):
        """
        Adds token subsets to the Hierarchy object for a corpus, and syncs it to the hierarchy schema in a Neo4j database

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type: str
            Annotation type to add subsets for
        subsets : iterable
            List of subsets to add for the annotation tokens
        """
        statement = self.get_token_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets + subsets)
        statement = self.set_token_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_tokens[annotation_type] = updated
        corpus_context.cache_hierarchy()

    def remove_token_subsets(self, corpus_context, annotation_type, subsets):
        """
        Removes token subsets to the Hierarchy object for a corpus, and syncs it to the hierarchy schema in a Neo4j database

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type: str
            Annotation type to remove subsets for
        subsets : iterable
            List of subsets to remove for the annotation tokens
        """
        statement = self.get_token_subset_template.format(type=annotation_type)
        res = list(corpus_context.execute_cypher(statement, corpus_name=corpus_context.corpus_name))
        try:
            cur_subsets = res[0]['subsets']
        except (IndexError, AttributeError):
            cur_subsets = []
        updated = set(cur_subsets) - set(subsets)
        statement = self.set_token_subset_template.format(type=annotation_type)
        corpus_context.execute_cypher(statement, subsets=sorted(updated),
                                      corpus_name=corpus_context.corpus_name)
        self.subset_tokens[annotation_type] = updated
        corpus_context.cache_hierarchy()

    def add_annotation_type(self, annotation_type, above=None, below=None):
        """
        Adds an annotation type to the Hierarchy object along with default type and token properties for the new
        annotation type

        Parameters
        ----------
        annotation_type : str
            Annotation type to add
        above : str
            Annotation type that is contained by the new annotation type, leave out if new annotation type is at the bottom
            of the hierarchy
        below : str
            Annotation type that contains the new annotation type, leave out if new annotation type is at the top
            of the hierarchy

        """
        self._data[above] = annotation_type
        self._data[annotation_type] = below
        self.token_properties[annotation_type] = {('id', str), ('label', str),
                                                  ('begin', float), ('end', float), ('duration', float)}
        self.type_properties[annotation_type] = {('label', str)}

    def remove_annotation_type(self, annotation_type):
        """
        Removes an annotation type from the hierarchy

        Parameters
        ----------
        annotation_type : str
            Annotation type to remove
        """
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
            del self.subannotations[annotation_type]

    def add_type_properties(self, corpus_context, annotation_type, properties):
        """
        Adds type properties for an annotation type and syncs it to a Neo4j database.  The list of properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type : str
            Annotation type to add type properties for
        properties : iterable
            Iterable of tuples of the form (property_name, Type)
        """
        set_template = 'n.{0} = ${0}'
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

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        SET {sets}""".format(type=annotation_type, sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        if annotation_type not in self.type_properties:
            self.type_properties[annotation_type] = {('id', str)}
        self.type_properties[annotation_type].update(k for k in properties)
        corpus_context.cache_hierarchy()

    def remove_type_properties(self, corpus_context, annotation_type, properties):
        """
        Removes type properties for an annotation type and syncs it to a Neo4j database.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type : str
            Annotation type to remove type properties for
        properties : iterable
            List of property names to remove
        """
        remove_template = 'n.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a:{type})-[:is_a]->(n:{type}_type)
        REMOVE {removes}""".format(type=annotation_type, removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        if annotation_type not in self.type_properties:
            self.type_properties[annotation_type] = {('id', str)}

        to_remove = set(x for x in self.type_properties[annotation_type] if x[0] in properties)
        self.type_properties[annotation_type].difference_update(to_remove)
        corpus_context.cache_hierarchy()

    def add_acoustic_properties(self, corpus_context, acoustic_type, properties):
        """
        Add acoustic properties to an encoded acoustic measure.  The list of properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        acoustic_type : str
            Acoustic measure to add properties for
        properties : iterable
            Iterable of tuples of the form (property_name, Type)
        """
        set_template = 'n.{0} = ${0}'
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

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)-[:has_acoustics]->(n:{type})
        SET {sets}""".format(type=acoustic_type, sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)
        if acoustic_type not in self.acoustic_properties:
            self.acoustic_properties[acoustic_type] = set()
        self.acoustic_properties[acoustic_type].update(k for k in properties)
        corpus_context.cache_hierarchy()

    def remove_acoustic_properties(self, corpus_context, acoustic_type, properties):
        """
        Remove acoustic properties to an encoded acoustic measure.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        acoustic_type : str
            Acoustic measure to remove properties for
        properties : iterable
            List of property names
        """
        remove_template = 'n.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)-[:has_acoustics]->(n:{type})
        REMOVE {removes}""".format(type=acoustic_type, removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        if acoustic_type not in self.acoustic_properties:
            self.acoustic_properties[acoustic_type] = {}
        to_remove = set(x for x in self.acoustic_properties[acoustic_type] if x[0] in properties)
        self.acoustic_properties[acoustic_type].difference_update(to_remove)
        corpus_context.cache_hierarchy()

    def add_token_properties(self, corpus_context, annotation_type, properties):
        """
        Adds token properties for an annotation type and syncs it to a Neo4j database.  The list of properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type : str
            Annotation type to add token properties for
        properties : iterable
            Iterable of tuples of the form (property_name, Type)
        """
        set_template = 'n.{0} = ${0}'
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

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(n:{type})
        SET {sets}""".format(type=annotation_type, sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)
        if annotation_type not in self.token_properties:
            self.token_properties[annotation_type] = {('id', str)}
        self.token_properties[annotation_type].update(k for k in properties)
        corpus_context.cache_hierarchy()

    def remove_token_properties(self, corpus_context, annotation_type, properties):
        """
        Removes token properties for an annotation type and syncs it to a Neo4j database.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type : str
            Annotation type to remove token properties for
        properties : iterable
            List of property names to remove
        """
        remove_template = 'n.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(n:{type})
        REMOVE {removes}""".format(type=annotation_type, removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        if annotation_type not in self.token_properties:
            self.token_properties[annotation_type] = {('id', str)}
        to_remove = set(x for x in self.token_properties[annotation_type] if x[0] in properties)
        self.token_properties[annotation_type].difference_update(to_remove)
        corpus_context.cache_hierarchy()

    def add_speaker_properties(self, corpus_context, properties):
        """
        Adds speaker properties to the Hierarchy object and syncs it to a Neo4j database.  The list of properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        properties : iterable
            Iterable of tuples of the form (property_name, Type)
        """
        set_template = 's.{0} = ${0}'
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

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)-[:spoken_by]->(s:Speaker)
        SET {sets}""".format(sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)
        to_add_names = [x[0] for x in properties]
        self.speaker_properties = {x for x in self.speaker_properties if x[0] not in to_add_names}
        self.speaker_properties.update(k for k in properties)
        corpus_context.cache_hierarchy()

    def remove_speaker_properties(self, corpus_context, properties):
        """
        Removes speaker properties and syncs it to a Neo4j database.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        properties : iterable
            List of property names to remove
        """
        remove_template = 's.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)-[:spoken_by]->(s:Speaker)
        REMOVE {removes}""".format(removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        to_remove = set(x for x in self.speaker_properties if x[0] in properties)
        self.speaker_properties.difference_update(to_remove)
        corpus_context.cache_hierarchy()

    def add_discourse_properties(self, corpus_context, properties):
        """
        Adds discourse properties to the Hierarchy object and syncs it to a Neo4j database.  The list of properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        properties : iterable
            Iterable of tuples of the form (property_name, Type)
        """
        set_template = 'd.{0} = ${0}'
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

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)-[:spoken_in]->(d:Discourse)
        SET {sets}""".format(sets=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        to_add_names = [x[0] for x in properties]
        self.discourse_properties = {x for x in self.discourse_properties if x[0] not in to_add_names}
        self.discourse_properties.update(k for k in properties)
        corpus_context.cache_hierarchy()

    def remove_discourse_properties(self, corpus_context, properties):
        """
        Removes discourse properties and syncs it to a Neo4j database.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        properties : iterable
            List of property names to remove
        """
        remove_template = 'd.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)-[:spoken_in]->(d:Discourse)
        REMOVE {removes}""".format(removes=', '.join(ps))
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        to_remove = set(x for x in self.discourse_properties if x[0] in properties)
        self.discourse_properties.difference_update(to_remove)
        corpus_context.cache_hierarchy()

    def keys(self):
        """
        Keys (linguistic types) of the hierarchy.

        Returns
        -------
        generator
            Keys of the hierarchy
        """
        return self._data.keys()

    def values(self):
        """
        Values (containing types) of the hierarchy.

        Returns
        -------
        generator
            Values of the hierarchy
        """
        return self._data.values()

    def items(self):
        """
        Key/value pairs for the hierarchy.

        Returns
        -------
        generator
            Items of the hierarchy
        """
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
        """
        Merge Hierarchies together.  If other is a dictionary, then only
        the hierarchical data is updated.

        Parameters
        ----------
        other : Hierarchy or dict
            Data to be merged in
        """
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
            self.speaker_properties.update(other.speaker_properties)
            self.discourse_properties.update(other.discourse_properties)

    @property
    def lowest(self):
        """
        Get the lowest annotation type of the Hierarchy

        Returns
        -------
        str
            Lowest annotation type
        """
        for k in self.keys():
            if k not in self.values():
                return k

    @property
    def highest(self):
        """
        Get the highest annotation type of the Hierarchy

        Returns
        -------
        str
            Highest annotation type
        """
        for k, v in self.items():
            if v is None:
                return k

    @property
    def highest_to_lowest(self):
        """
        Get a list of annotation types sorted from highest to lowest

        Returns
        -------
        list
            Annotation types from highest to lowest
        """
        ats = [self.highest]
        while len(ats) < len(self.keys()):
            for k, v in self.items():
                if v == ats[-1]:
                    ats.append(k)
                    break
        return ats

    @property
    def lowest_to_highest(self):
        """
        Get a list of annotation types sorted from lowest to highest

        Returns
        -------
        list
            Annotation types from lowest to highest
        """
        ats = [self.lowest]
        while len(ats) < len(self.keys()):
            ats.append(self[ats[-1]])
        return ats

    def get_lower_types(self, annotation_type):
        """
        Get all annotation types that are lower than the specified annotation type

        Parameters
        ----------
        annotation_type : str
            Annotation type from which to get lower annotation types

        Returns
        -------
        list
            List of all annotation types that are lower the specified annotation type
        """
        lower = []
        found = False
        for t in self.highest_to_lowest:
            if t == annotation_type:
                found = True
                continue
            if found:
                lower.append(t)
        return lower

    def get_higher_types(self, annotation_type):
        """
        Get all annotation types that are higher than the specified annotation type

        Parameters
        ----------
        annotation_type : str
            Annotation type from which to get higher annotation types

        Returns
        -------
        list
            List of all annotation types that are higher the specified annotation type
        """
        higher = []
        found = False
        for t in self.lowest_to_highest:
            if t == annotation_type:
                found = True
                continue
            if found:
                higher.append(t)
        return higher

    def has_subannotation_type(self, subannotation_type):
        """
        Check whether the Hierarchy has a subannotation type

        Parameters
        ----------
        subannotation_type : str
            Name of subannotation to check for

        Returns
        -------
        bool
            True if subannotation type is present
        """
        return subannotation_type in self.subannotation_properties

    def has_subannotation_property(self, subannotation_type, property_name):
        """
        Check whether the Hierarchy has a property associated with a subannotation type

        Parameters
        ----------
        subannotation_type : str
            Name of subannotation to check
        property_name : str
            Name of the property to check for

        Returns
        -------
        bool
            True if subannotation type has the given property name
        """
        if not self.has_subannotation_type(subannotation_type):
            return False
        return property_name in [x[0] for x in self.subannotation_properties[subannotation_type]]

    def add_subannotation_type(self, corpus_context, annotation_type, subannotation_type, properties=None):
        """
        Adds subannotation type for a given annotation type to the Hierarchy object and syncs it to a Neo4j database.
        The list of optional properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        annotation_type : str
            Annotation type to add a subannotation to
        subannotation_type : str
            Name of the subannotation type
        properties : iterable
            Optional iterable of tuples of the form (property_name, Type)
        """
        if properties is None:
            properties = []
        if subannotation_type in self.subannotation_properties:
            raise (HierarchyError('The subannotation_type {} is already specified for another linguistic type.'
                                  ' Please use a different name.'.format(subannotation_type)))
        if annotation_type not in self.subannotations:
            self.subannotations[annotation_type] = set()
        self.subannotations[annotation_type].add(subannotation_type)
        self.subannotation_properties[subannotation_type] = set(k for k in properties)
        if properties:
            set_template = 's.{0} = ${0}'
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
            statement = """MATCH (c:Corpus), (c)<-[:contained_by*]-(a:{a_type}) WHERE c.name = $corpus_name
                    WITH a
                    CREATE (a)<-[:annotates]-(s:{s_type})
                    WITH s
                    SET {sets}""".format(sets=', '.join(ps), a_type= annotation_type, s_type=subannotation_type)
            corpus_context.execute_cypher(statement,
                                          corpus_name=corpus_context.corpus_name, **kwargs)

        else:
            statement = """MATCH (c:Corpus), (c)<-[:contained_by*]-(a:{a_type}) WHERE c.name = $corpus_name
                    WITH a
                    MERGE (a)<-[:annotates]-(s:{s_type})""".format(a_type= annotation_type, s_type=subannotation_type)
            corpus_context.execute_cypher(statement,
                                          corpus_name=corpus_context.corpus_name)
        corpus_context.cache_hierarchy()

    def remove_subannotation_type(self, corpus_context, subannotation_type):
        """
        Remove a subannotation type from the Hierarchy object and sync it to a Neo4j database.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        subannotation_type : str
            Subannotation type to remove
        """
        try:
            del self.subannotation_properties[subannotation_type]
        except KeyError:
            pass
        for k, v in self.subannotations.items():
            if subannotation_type in v:
                self.subannotations[k] = v - {subannotation_type}
        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a)<-[:annotates]-(s:{s_type})
        DETACH DELETE s""".format(s_type=subannotation_type)
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        corpus_context.cache_hierarchy()

    def add_subannotation_properties(self, corpus_context, subannotation_type, properties):
        """
        Adds properties for a subannotation type to the Hierarchy object and syncs it to a Neo4j database.
        The list of properties are tuples
        of the form (property_name, Type), where ``property_name`` is a string and ``Type`` is a Python type class, like
        ``bool``, ``str``, ``list``, or ``float``.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        subannotation_type : str
            Name of the subannotation type
        properties : iterable
            Iterable of tuples of the form (property_name, Type)
        """
        set_template = 's.{0} = ${0}'
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

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a)<-[:annotates]-(s:{s_type})
        SET {sets}""".format(sets=', '.join(ps), s_type=subannotation_type)
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name, **kwargs)

        self.subannotation_properties[subannotation_type].update(k for k in properties)
        corpus_context.cache_hierarchy()

    def remove_subannotation_properties(self, corpus_context, subannotation_type, properties):
        """
        Removes properties for a subannotation type to the Hierarchy object and syncs it to a Neo4j database.

        Parameters
        ----------
        corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
            CorpusContext to use for updating Neo4j database
        subannotation_type : str
            Name of the subannotation type
        properties : iterable
            List of property names to remove
        """
        remove_template = 's.{0}'
        ps = []
        for k in properties:
            ps.append(remove_template.format(k))

        statement = """MATCH (c:Corpus) WHERE c.name = $corpus_name
        MATCH (c)<-[:contained_by*]-(a)<-[:annotates]-(s:{s_type})
        REMOVE {removes}""".format(removes=', '.join(ps), s_type=subannotation_type)
        corpus_context.execute_cypher(statement,
                                      corpus_name=corpus_context.corpus_name)
        to_remove = set(x for x in self.subannotation_properties[subannotation_type] if x[0] in properties)
        self.subannotation_properties[subannotation_type].difference_update(to_remove)
        corpus_context.cache_hierarchy()

    def has_speaker_property(self, key):
        """
        Check for whether speakers have a given property

        Parameters
        ----------
        key : str
            Property to check for

        Returns
        -------
        bool
            True if speakers have the given property
        """
        for name, t in self.speaker_properties:
            if name == key:
                return True
        return False

    def has_discourse_property(self, key):
        """
        Check for whether discourses have a given property

        Parameters
        ----------
        key : str
            Property to check for

        Returns
        -------
        bool
            True if discourses have the given property
        """
        for name, t in self.discourse_properties:
            if name == key:
                return True
        return False

    def has_token_property(self, annotation_type, key):
        """
        Check whether a given annotation type has a given token property.

        Parameters
        ----------
        annotation_type : str
            Annotation type to check for the given token property
        key : str
            Property to check for

        Returns
        -------
        bool
            True if the annotation type has the given token property
        """
        if annotation_type not in self.token_properties:
            return False
        for name, t in self.token_properties[annotation_type]:
            if name == key:
                return True
        return False

    def has_type_property(self, annotation_type, key):
        """
        Check whether a given annotation type has a given type property.

        Parameters
        ----------
        annotation_type : str
            Annotation type to check for the given type property
        key : str
            Property to check for

        Returns
        -------
        bool
            True if the annotation type has the given type property
        """
        if annotation_type not in self.type_properties:
            return False
        for name, t in self.type_properties[annotation_type]:
            if name == key:
                return True
        return False

    def has_type_subset(self, annotation_type, key):
        """
        Check whether a given annotation type has a given type subset.

        Parameters
        ----------
        annotation_type : str
            Annotation type to check for the given type subset
        key : str
            Subset to check for

        Returns
        -------
        bool
            True if the annotation type has the given type subset
        """
        if annotation_type not in self.subset_types:
            return False
        return key in self.subset_types[annotation_type]

    def has_token_subset(self, annotation_type, key):
        """
        Check whether a given annotation type has a given token subset.

        Parameters
        ----------
        annotation_type : str
            Annotation type to check for the given token subset
        key : str
            Subset to check for

        Returns
        -------
        bool
            True if the annotation type has the given token subset
        """
        if annotation_type not in self.subset_tokens:
            return False
        return key in self.subset_tokens[annotation_type]

    @property
    def word_name(self):
        """
        Shortcut for returning the annotation type matching "word"

        Returns
        -------
        str or None
            Annotation type that begins with "word"
        """
        for at in self.annotation_types:
            if at.startswith('word'):
                return at
        return None

    @property
    def phone_name(self):
        """
        Alias function for getting the lowest annotation type

        Returns
        -------
        str
            Name of the lowest annotation type
        """
        return self.lowest
