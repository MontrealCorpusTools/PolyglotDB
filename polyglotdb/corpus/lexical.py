
from .base import BaseContext

from ..io.importer import lexicon_data_to_csvs, import_lexicon_csvs

class LexicalContext(BaseContext):
    def enrich_lexicon(self, lexicon_data, type_data = None, case_sensitive = False):
        if type_data is None:
            type_data = {k: type(v) for k,v in next(iter(lexicon_data.values())).items()}
        if case_sensitive:
            labels = set(self.lexicon.all())
        else:
            labels = set(x.lower() for x in self.lexicon.all())
        lexicon_data = {k: v for k,v in lexicon_data.items() if k in labels}
        lexicon_data_to_csvs(self, lexicon_data, case_sensitive = case_sensitive)
        import_lexicon_csvs(self, type_data, case_sensitive = case_sensitive)
        self.hierarchy.add_type_properties(self, self.word_name, type_data.items())
        self.encode_hierarchy()

    def reset_lexicon(self):
        pass
