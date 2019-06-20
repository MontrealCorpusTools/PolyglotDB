from ..annotations.attributes.base import AnnotationNode
from ..discourse.attributes import DiscourseNode
from ..speaker.attributes import SpeakerNode
from ..base.func import Min, Max, Count


class MetaDataQuery(object):
    """
    Class for generating a Cypher query to return information about metadata in the corpus

    Parameters
    ----------
    corpus : :class:`~polyglotdb.corpus.structured.StructuredContext`
        The corpus to query
    to_find : :class:`~polyglotdb.query.base.Node`
        Name of the annotation type to search for
    """
    query_template = '''{match}
    {where}
    {optional_match}
    {with}
    {return}'''

    def __init__(self, corpus, to_find):
        self.corpus = corpus
        self.to_find = to_find

    def factors(self):
        """
        Get a list of all Attributes on the specified Node that are factors (i.e., use strings instead of
        integers/floats/booleans)

        Returns
        -------
        list
            All attributes that use strings
        """
        hierarchy = self.corpus.hierarchy
        factors = []
        if isinstance(self.to_find, AnnotationNode):
            factors.extend(x[0] for x in hierarchy.token_properties[self.to_find.node_type] if x[1] == str)
            factors.extend(x[0] for x in hierarchy.type_properties[self.to_find.node_type] if x[1] == str)
        elif isinstance(self.to_find, DiscourseNode):
            factors.extend(x[0] for x in hierarchy.discourse_properties if x[1] == str)
        elif isinstance(self.to_find, SpeakerNode):
            factors.extend(x[0] for x in hierarchy.speaker_properties if x[1] == str)
        return factors

    def numerics(self):
        """
        Get a list of all Attributes that use numerics (i.e., floats/integers instead of strings/booleans)

        Returns
        -------
        list
            All attributes that use floats and integers
        """
        hierarchy = self.corpus.hierarchy
        numerics = []
        if isinstance(self.to_find, AnnotationNode):
            numerics.extend(x[0] for x in hierarchy.token_properties[self.to_find.node_type] if x[1] in (float, int))
            numerics.extend(x[0] for x in hierarchy.type_properties[self.to_find.node_type] if x[1] in (float,int))
        elif isinstance(self.to_find, DiscourseNode):
            numerics.extend(x[0] for x in hierarchy.discourse_properties if x[1] in (float,int))
        elif isinstance(self.to_find, SpeakerNode):
            numerics.extend(x[0] for x in hierarchy.speaker_properties if x[1] in (float,int))
        return numerics

    def grouping_factors(self):
        """
        Get a list of all factors that have token counts greater than 1

        Returns
        -------
        list
            All factors that can be used for reasonable grouping

        """
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
            elif isinstance(self.to_find, SpeakerNode):
                q = self.corpus.query_speakers().group_by(getattr(self.to_find, f).column_name('label')).aggregate(Count())
                if any(x['count_all'] > 1 for x in q):
                    grouping.append(f)
        return grouping

    def levels(self, attribute):
        """
        Get the levels (i.e., string values) of a factor

        Parameters
        ----------
        attribute : :class:`~polyglotdb.query.base.Attribute`
            Attribute to get levels of

        Returns
        -------
        list
            All the levels of the attribute
        """
        if attribute.label in self.numerics():
            raise Exception('Levels is only valid for factors.')
        if isinstance(self.to_find, AnnotationNode):
            q = self.corpus.query_graph(self.to_find).group_by(attribute.column_name('label')).aggregate(Count())
        elif isinstance(self.to_find, DiscourseNode):
            q = self.corpus.query_discourses().group_by(attribute.column_name('label')).aggregate(Count())
        elif isinstance(self.to_find, SpeakerNode):
            q = self.corpus.query_speakers().group_by(attribute.column_name('label')).aggregate(Count())
        return [x['label'] for x in q]

    def range(self, attribute):
        """
        Get the range (minimum and maximum) of a numeric attribute

        Parameters
        ----------
        attribute : :class:`~polyglotdb.query.base.Attribute`
            Attribute to get range over

        Returns
        -------
        float
            Minimum
        float
            Maximum
        """
        if attribute.label in self.factors():
            raise Exception('Range function is only valid for numerics.')
        if isinstance(self.to_find, AnnotationNode):
            q = self.corpus.query_graph(self.to_find).aggregate(Min(attribute).column_name('min'), Max(attribute).column_name('max'))
        if isinstance(self.to_find, DiscourseNode):
            q = self.corpus.query_discourses().aggregate(Min(attribute).column_name('min'), Max(attribute).column_name('max'))
        if isinstance(self.to_find, SpeakerNode):
            q = self.corpus.query_speakers().aggregate(Min(attribute).column_name('min'), Max(attribute).column_name('max'))
        return q['min'], q['max']