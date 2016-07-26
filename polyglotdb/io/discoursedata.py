
class DiscourseData(object):
    """
    Class for collecting information about a discourse to be loaded

    Parameters
    ----------
    name : str
        Identifier for the discourse
    annotation_types : list
        List of :class:`BaseAnnotationType` objects
    hierarchy : :class:`~polyglotdb.structure.Hierarchy`
        Details of how linguistic types relate to one another

    Attributes
    ----------
    name : str
        Identifier for the discourse
    data : dict
        Dictionary containing :class:`BaseAnnotationType` objects indexed by
        their name
    segment_type : str or None
        Identifier of the segment linguistic annotation, if it exists
    wav_path : str or None
        Path to sound file if it exists

    """
    def __init__(self, name, annotation_types, hierarchy):
        self.name = name
        self.data = annotation_types
        self.speaker_channel_mapping = {}

        self.segment_type = None
        for k,v in self.data.items():
            if k not in hierarchy.values() and not v.is_word:
                self.segment_type = k
        self.hierarchy = hierarchy
        self.wav_path = None
        for k, at in self.data.items():
            self.hierarchy.type_properties[at.name] = at.type_properties
            self.hierarchy.token_properties[at.name] = at.token_properties

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, item):
        return item in self.data

    def highest_to_lowest(self):
        """
        orders hierarchy highest to lowest

        Returns
        -------
        ats : dict
            the ordered hierarchy
        """
        ats = []
        for k,v in self.hierarchy.items():
            if v is None:
                ats.append(k)
                break
        while len(ats) < len(self.hierarchy.keys()):
            for k,v in self.hierarchy.items():
                if v == ats[-1]:
                    ats.append(k)
                    break
        return ats

    @property
    def token_headers(self):
        headers = {}
        for x in self.annotation_types:
            token_header = ['begin', 'end', 'type_id', 'id', 'previous_id', 'speaker', 'discourse']
            token_header += sorted(self[x].token_property_keys)
            supertype = self[x].supertype
            if supertype is not None:
                token_header.append(supertype)
            headers[x] = token_header
        return headers

    @property
    def speakers(self):
        """
        Returns speakers from a discourse
        """
        speakers = set()
        for x in self.values():
            speakers.update(x.speakers)
        return speakers

    @property
    def annotation_types(self):
        """ Returns corpus annotation types"""
        return self.keys()

    def keys(self):
        """ Returns corpus keys"""
        return self.data.keys()

    def values(self):
        """ Returns tuple of values in corpus"""
        return (self.data[x] for x in self.keys())

    def items(self):
        """ Returns tuple of items in corpus"""
        return ((x, self.data[x]) for x in self.keys())

    def types(self, corpus_name):
        """ Returns tuple of types and type headers

        Parameters
        ----------
        corpus_name : str
            the name of the corpus"""
        types = {}
        type_headers = {}
        for k, v in self.items():
            types[k] = set()
            for w in v:
                if k not in type_headers:
                    type_headers[k] = ['id'] + w.type_keys()
                id = w.sha(corpus_name)
                props = tuple([id] + [x for x in w.type_values()])
                types[k].add(props)
        return types, type_headers
