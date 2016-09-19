
from .base import BaseContext
from .audio import AudioContext
from .importable import ImportContext
from .featured import FeaturedContext
from .lexical import LexicalContext
from .pause import PauseContext
from .utterance import UtteranceContext
from .structured import StructuredContext
from .syllabic import SyllabicContext
from .spoken import SpokenContext
from .summarized import SummarizedContext


class CorpusContext(StructuredContext, ImportContext, FeaturedContext, LexicalContext,
                    PauseContext, UtteranceContext, AudioContext,
                    SyllabicContext, SpokenContext, SummarizedContext):
    """
    Main corpus context, inherits from the more specialized contexts.

    Parameters
    ----------

    *args
        Either a CorpusConfig object or sequence of arguments to be
        passed to a CorpusConfig object
    **kwargs
        sequence of keyword arguments to be passed to a CorpusConfig object


    """

    pass



