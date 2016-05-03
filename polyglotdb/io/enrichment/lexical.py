
from .helper import parse_file

def enrich_lexicon_from_csv(corpus_context, path, case_sensitive = False):
    data, type_data = parse_file(path, case_sensitive = case_sensitive)
    corpus_context.enrich_lexicon(data, type_data, case_sensitive = case_sensitive)
