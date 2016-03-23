
from .base import BaseContext

from ..io.importer import lexicon_data_to_csvs, import_lexicon_csvs

class LexicalContext(BaseContext):
    def enrich_lexicon(self, lexicon_data):
        type_data = {k: type(v) for k,v in next(iter(lexicon_data.values())).items()}
        lexicon_data_to_csvs(self, lexicon_data)
        import_lexicon_csvs(self, type_data)
        self.hierarchy.type_properties[self.word_name].update(type_data.items())
        self.encode_hierarchy()
