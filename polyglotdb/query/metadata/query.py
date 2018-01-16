from ..annotations.attributes.base import AnnotationNode
from ..base.func import Min, Max


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
        hierarchy = self.corpus.hierarchy
        factors = []
        if isinstance(self.to_find, AnnotationNode):
            factors.extend(x[0] for x in hierarchy.token_properties[self.to_find.node_type] if x[1] == '')
            factors.extend(x[0] for x in hierarchy.type_properties[self.to_find.node_type] if x[1] == '')
        return factors

    def numerics(self):
        hierarchy = self.corpus.hierarchy
        numerics = []
        if isinstance(self.to_find, AnnotationNode):
            numerics.extend(x[0] for x in hierarchy.token_properties[self.to_find.node_type] if x[1] == 0)
            numerics.extend(x[0] for x in hierarchy.type_properties[self.to_find.node_type] if x[1] == 0)
        return numerics

    def grouping_factors(self):
        grouping = []
        for f in self.factors():
            if isinstance(self.to_find, AnnotationNode):
                q = self.corpus.query_graph(self.to_find).group_by(f.column_name('label')).count()
                if any(x['count'] > 1 for x in q.all()):
                    grouping.append(f)
        return grouping

    def levels(self, attribute):
        if attribute.label in self.numerics():
            raise Exception('Levels is only valid for factors.')
        if isinstance(self.to_find, AnnotationNode):
            q = self.corpus.query_graph(self.to_find).group_by(attribute.column_name('label')).count()
        return [x['label'] for x in q.all()]

    def range(self, attribute):
        if attribute.label in self.factors():
            raise Exception('Range function is only valid for numerics.')
        if isinstance(self.to_find, AnnotationNode):
            q = self.corpus.query_graph(self.to_find).aggregate(Min(attribute).column_name('min'), Max(attribute).column_name('max'))
        return q['min'], q['max']