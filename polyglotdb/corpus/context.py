from .annotated import AnnotatedContext


class CorpusContext(AnnotatedContext):
    """
    Main corpus context, inherits from the more specialized contexts.

    Parameters
    ----------
    args : args
        Either a CorpusConfig object or sequence of arguments to be
        passed to a CorpusConfig object
    kwargs : kwargs
        sequence of keyword arguments to be passed to a CorpusConfig object
    """
    pass
