

from .audio import AudioContext
from .importable import ImportContext
from .lexical import LexicalContext
from .pause import PauseContext
from .utterance import UtteranceCorpus
from .structured import StructuredContext
from .syllabic import SyllabicContext


class CorpusContext(StructuredContext, ImportContext, LexicalContext,
                    PauseContext, UtteranceCorpus, AudioContext,
                    SyllabicContext):
    pass



