from ..base import BaseQuery

from .attributes import SpeakerNode


class SpeakerQuery(BaseQuery):
    def __init__(self, corpus):
        to_find = SpeakerNode(corpus=corpus.corpus_name, hierarchy=corpus.hierarchy)
        super(SpeakerQuery, self).__init__(corpus, to_find)
