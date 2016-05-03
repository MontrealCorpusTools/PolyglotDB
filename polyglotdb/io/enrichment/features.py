
from .helper import parse_file

def enrich_features_from_csv(corpus_context, path):
    data, type_data = parse_file(path)
    corpus_context.enrich_features(data, type_data)
