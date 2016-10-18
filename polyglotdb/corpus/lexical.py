
from ..io.importer import lexicon_data_to_csvs, import_lexicon_csvs
import time
class LexicalContext(object):
    def enrich_lexicon(self, lexicon_data, type_data = None, case_sensitive = False):
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
        for k,v in next(iter(lexicon_data.values())).items():
            print(k,v)

        t0 = time.clock()
        if type_data is None:
            type_data = {k: type(v) for k,v in next(iter(lexicon_data.values())).items()}
        print(type_data)
        print("time to get type_data in enrich_lexicon: {}".format(time.clock()-t0))
        if case_sensitive:
            labels = set(self.lexicon.words())
        else:
            labels = set(x.lower() for x in self.lexicon.words())
        print("time to get words in enrich_lexicon: {}".format(time.clock()-t0))
        lexicon_data = {k: v for k,v in lexicon_data.items() if k in labels}
        print("time to get lexicon_data in enrich_lexicon: {}".format(time.clock()-t0))
        self.lexicon.add_properties(self.word_name, lexicon_data, type_data, case_sensitive = case_sensitive)
        print("time to add properties in enrich_lexicon: {}".format(time.clock()-t0))
        lexicon_data_to_csvs(self, lexicon_data, case_sensitive = case_sensitive)
        print("time to write csvs in enrich_lexicon: {}".format(time.clock()-t0))
        import_lexicon_csvs(self, type_data, case_sensitive = case_sensitive)
        print("time to import csvs in enrich_lexicon: {}".format(time.clock()-t0))
        self.hierarchy.add_type_properties(self, self.word_name, type_data.items())
        print("time to add properties in enrich_lexicon: {}".format(time.clock()-t0))
        self.encode_hierarchy()
        print("time to encode hierarchy in enrich_lexicon: {}".format(time.clock()-t0))
    def reset_lexicon(self):
        pass
