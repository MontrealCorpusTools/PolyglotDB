from ..io.importer import lexicon_data_to_csvs, import_lexicon_csvs
from ..io.enrichment.lexical import enrich_lexicon_from_csv
from .spoken import SpokenContext


class LexicalContext(SpokenContext):
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

    def reset_lexicon(self):
        pass

    def enrich_lexicon_from_csv(self, path, case_sensitive=False):
        """
        Enriches lexicon from a csv file

        Parameters
        ----------
        path : str
            the path to the csv file
        case_sensitive : boolean
            Defaults to false
        """
        enrich_lexicon_from_csv(self, path, case_sensitive)