from ..base import BaseQuery

from .attributes import SpeakerNode
from .cypher import query_to_cypher


class SpeakerQuery(BaseQuery):
    def __init__(self, corpus):
        to_find = SpeakerNode(corpus=corpus.corpus_name, hierarchy=corpus.hierarchy)
        super(SpeakerQuery, self).__init__(corpus, to_find)

    def cypher(self):
        return query_to_cypher(self)
