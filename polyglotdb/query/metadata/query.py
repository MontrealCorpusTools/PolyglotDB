from ..annotations.attributes.base import AnnotationNode
from ..discourse.attributes import DiscourseNode
from ..base.func import Min, Max, Count


class MetaDataQuery(object):
    query_template = '''{match}
    {where}
    {optional_match}
    {with}
    {return}'''

    def __init__(self, corpus, to_find):
        """

        Parameters
        ----------
        corpus : :class:`~polyglotdb.corpus.CorpusContext`
            The corpus to query
        to_find : :class:`~polyglotdb.query.base.Node`
            Name of the annotation type to search for
        """
        self.corpus = corpus
        self.to_find = to_find

    def factors(self):
        print('hello')
        hierarchy = self.corpus.hierarchy
        factors = []
        if isinstance(self.to_find, AnnotationNode):
            factors.extend(x[0] for x in hierarchy.token_properties[self.to_find.node_type] if x[1] == str)
            factors.extend(x[0] for x in hierarchy.type_properties[self.to_find.node_type] if x[1] == str)
        elif isinstance(self.to_find, DiscourseNode):
            print(hierarchy.discourse_properties)
            factors.extend(x[0] for x in hierarchy.discourse_properties if x[1] == str)
        print(factors)
        return factors

    def numerics(self):
        hierarchy = self.corpus.hierarchy
        numerics = []
        if isinstance(self.to_find, AnnotationNode):
            numerics.extend(x[0] for x in hierarchy.token_properties[self.to_find.node_type] if x[1] in (float, int))
            numerics.extend(x[0] for x in hierarchy.type_properties[self.to_find.node_type] if x[1] == (float,int))
        return numerics

    def grouping_factors(self):
        grouping = []
        for f in self.factors():
            if isinstance(self.to_find, AnnotationNode):
                q = self.corpus.query_graph(self.to_find).group_by(f.column_name('label')).aggregate(Count())
                if any(x['count_all'] > 1 for x in q):
                    grouping.append(f)
            elif isinstance(self.to_find, DiscourseNode):
                q = self.corpus.query_discourses().group_by(getattr(self.to_find, f).column_name('label')).aggregate(Count())
                if any(x['count_all'] > 1 for x in q):
                    grouping.append(f)
        return grouping

    def levels(self, attribute):
        if attribute.label in self.numerics():
            raise Exception('Levels is only valid for factors.')
        if isinstance(self.to_find, AnnotationNode):
            q = self.corpus.query_graph(self.to_find).group_by(attribute.column_name('label')).aggregate(Count())
        elif isinstance(self.to_find, DiscourseNode):
            q = self.corpus.query_discourses().group_by(attribute.column_name('label')).aggregate(Count())
        return [x['label'] for x in q]

    def range(self, attribute):
        if attribute.label in self.factors():
            raise Exception('Range function is only valid for numerics.')
        if isinstance(self.to_find, AnnotationNode):
            q = self.corpus.query_graph(self.to_find).aggregate(Min(attribute).column_name('min'), Max(attribute).column_name('max'))
        return q['min'], q['max']