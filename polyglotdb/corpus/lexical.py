
from ..io.importer import lexicon_data_to_csvs, import_lexicon_csvs


class LexicalContext(object):
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
        self.lexicon.add_properties(self.word_name, lexicon_data, type_data, case_sensitive=case_sensitive)
        lexicon_data_to_csvs(self, lexicon_data, case_sensitive=case_sensitive)
        import_lexicon_csvs(self, type_data, case_sensitive=case_sensitive)
        self.hierarchy.add_type_properties(self, self.word_name, type_data.items())
        self.encode_hierarchy()

    def reset_lexicon(self):
        pass
