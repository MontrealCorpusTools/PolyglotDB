
from .helper import parse_file


def enrich_speakers_from_csv(corpus_context, path):
    """
    Enriches speakers from a csv file

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
        the corpus being enriched
    path : str
        the path to the csv file
    """
    data, type_data = parse_file(path, labels=corpus_context.speakers)
    if not data:
        return
    corpus_context.enrich_speakers(data, type_data)


def enrich_discourses_from_csv(corpus_context, path):
    """
    Enriches discourses from a csv file

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
        the corpus being enriched
    path : str
        the path to the csv file
    """
    data, type_data = parse_file(path)
    corpus_context.enrich_discourses(data, type_data)
