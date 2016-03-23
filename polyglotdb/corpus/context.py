

from .audio import AudioContext
from .importable import ImportContext
from .lexical import LexicalContext
from .pause import PauseContext
from .utterance import UtteranceCorpus
from .structured import StructuredContext


class CorpusContext(StructuredContext, ImportContext, LexicalContext,
                    PauseContext, UtteranceCorpus, AudioContext):

    pass



