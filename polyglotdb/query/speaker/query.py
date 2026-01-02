from polyglotdb.query.base import BaseQuery
from polyglotdb.query.speaker.attributes import SpeakerNode


class SpeakerQuery(BaseQuery):
    """
    Class for generating a Cypher query over speakers
    """

    def __init__(self, corpus):
        to_find = SpeakerNode(corpus=corpus.corpus_name, hierarchy=corpus.hierarchy)
        super(SpeakerQuery, self).__init__(corpus, to_find)
