from .helper import parse_file


def enrich_lexicon_from_csv(corpus_context, path, case_sensitive=False):
    """
    Enriches lexicon from a csv file

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
        the corpus being enriched
    path : str
        the path to the csv file
    case_sensitive : boolean
        Defaults to false
    """
    if case_sensitive:
        labels = set(corpus_context.words)
    else:
        labels = set(x.lower() for x in corpus_context.words)
    data, type_data = parse_file(path, labels=labels, case_sensitive=case_sensitive)
    if data:
        corpus_context.enrich_lexicon(data, type_data, case_sensitive=case_sensitive)
