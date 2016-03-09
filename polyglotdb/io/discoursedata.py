
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
    def speakers(self):
        speakers = set()
        for x in self.values():
            speakers.update(x.speakers)
        return speakers

    @property
    def annotation_types(self):
        return self.keys()

    def keys(self):
        return self.data.keys()

    def values(self):
        return (self.data[x] for x in self.keys())

    def items(self):
        return ((x, self.data[x]) for x in self.keys())
