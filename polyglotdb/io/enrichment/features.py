from .helper import parse_file


def enrich_features_from_csv(corpus_context, path):
    """
    Enriches corpus from a csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus being enriched
    path : str
        the path to the csv file
    """
    data, type_data = parse_file(path)
    corpus_context.enrich_features(data, type_data)
