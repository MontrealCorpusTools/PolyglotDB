
from .base import BaseContext
from .audio import AudioContext
from .importable import ImportContext
from .lexical import LexicalContext
from .pause import PauseContext
from .utterance import UtteranceContext
from .structured import StructuredContext
from .syllabic import SyllabicContext
from .spoken import SpokenContext


class CorpusContext(BaseContext, StructuredContext, ImportContext, LexicalContext,
                    PauseContext, UtteranceContext, AudioContext,
                    SyllabicContext, SpokenContext):
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



