from ..io.importer import lexicon_data_to_csvs, import_lexicon_csvs
from ..io.enrichment.lexical import enrich_lexicon_from_csv, parse_file
from .spoken import SpokenContext


class LexicalContext(SpokenContext):
    """
    Class that contains methods for dealing specifically with words
    """
    def enrich_lexicon(self, lexicon_data, type_data=None, case_sensitive=False):
        """
        adds properties to lexicon, adds properties to hierarchy

        Parameters
        ----------
        lexicon_data : dict
            the data in the lexicon
        type_data : dict
            default to None
        case_sensitive : bool
            default to False
        """
        if type_data is None:
            type_data = {k: type(v) for k, v in next(iter(lexicon_data.values())).items()}
        removed = [x for x in type_data.keys() if self.hierarchy.has_type_property(self.word_name, x)]
        type_data = {k: v for k,v in type_data.items() if k not in removed}
        if not type_data:
            return
        lexicon_data_to_csvs(self, lexicon_data, case_sensitive=case_sensitive)
        import_lexicon_csvs(self, type_data, case_sensitive=case_sensitive)
        self.hierarchy.add_type_properties(self, self.word_name, type_data.items())
        self.encode_hierarchy()

    def enrich_lexicon_from_csv(self, path, case_sensitive=False):
        """
        Enriches lexicon from a CSV file

        Parameters
        ----------
        path : str
            the path to the csv file
        case_sensitive : boolean
            Defaults to false
        """
        enrich_lexicon_from_csv(self, path, case_sensitive)

    def reset_lexicon_csv(self, path):
        """
        Remove properties that were encoded via a CSV file

        Parameters
        ----------
        path : str
            CSV file to get property names from
        """
        data, type_data = parse_file(path, labels=[])
        word = getattr(self, 'lexicon_' + self.word_name)
        q = self.query_lexicon(word)
        property_names = [x for x in type_data.keys()]
        q.set_properties(**{x: None for x in property_names})
        self.hierarchy.remove_type_properties(self, self.word_name, property_names)
        self.encode_hierarchy()

