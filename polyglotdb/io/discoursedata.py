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
        for k, v in self.data.items():
            if k not in hierarchy.values() and not v.is_word:
                self.segment_type = k
        self.hierarchy = hierarchy
        self.wav_path = None
        for k, at in self.data.items():
            self.hierarchy.type_properties[at.name] = at.type_properties
            self.hierarchy.type_properties[at.name].add(('id', type('')))
            self.hierarchy.type_properties[at.name].add(('label', type('')))
            if not at.token_properties:
                self.hierarchy.token_properties[at.name] = set((x, type(None)) for x in at.token_property_keys if x not in ['id', 'label', 'begin', 'end'])
            else:
                self.hierarchy.token_properties[at.name] = at.token_properties
            self.hierarchy.token_properties[at.name].add(('id', type('')))
            self.hierarchy.token_properties[at.name].add(('label', type('')))
            self.hierarchy.token_properties[at.name].add(('begin', type(0.0)))
            self.hierarchy.token_properties[at.name].add(('end', type(0.0)))

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
        for k, v in self.hierarchy.items():
            if v is None:
                ats.append(k)
                break
        while len(ats) < len(self.hierarchy.keys()):
            for k, v in self.hierarchy.items():
                if v == ats[-1]:
                    ats.append(k)
                    break
        return ats

    @property
    def token_headers(self):
        """
        Get the headers for the CSV file for importing annotation tokens

        Returns
        -------
        list
            Token headers
        """
        headers = {}
        for x in self.annotation_types:
            token_header = ['begin', 'end', 'type_id', 'id', 'previous_id', 'speaker', 'discourse', 'label']
            token_header += sorted(
                y[0] for y in self.hierarchy.token_properties[x] if y[0] not in ['label', 'begin', 'end', 'id'])
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
        return sorted(speakers)

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
        """
        Get all the types in the discourse and return them along with header information

        Parameters
        ----------
        corpus_name : str
            the name of the corpus

        Returns
        -------
        dict
            Type data
        list
            Type headers
        """
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
