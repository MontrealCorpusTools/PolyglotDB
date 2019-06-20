from ..base import BaseQuery

from .attributes import DiscourseNode


class DiscourseQuery(BaseQuery):
    """
    Class for generating a Cypher query over discourses
    """
    def __init__(self, corpus):
        to_find = DiscourseNode(corpus=corpus.corpus_name, hierarchy=corpus.hierarchy)
        super(DiscourseQuery, self).__init__(corpus, to_find)
