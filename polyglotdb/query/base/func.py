
class AggregateFunction(object):
    function = ''
    template = '{function}({property})'
    collection_templates = {'sum': 'reduce(count = 0, n in {property} | count + n)',
                            'avg': 'reduce(count = 0, n in {property} | count + n) / toFloat(size({property}))',
                            'count': 'size({property})'}

    def __init__(self, attribute=None):
        self.attribute = attribute
        self.output_label = None

    def __hash__(self):
        return hash((self.function, self.attribute))

    @property
    def nodes(self):
        if self.attribute is None:
            return []
        return self.attribute.nodes

    @property
    def acoustic(self):
        """
        Returns
        -------
        :class:`~polyglotdb.graph.attributes.Attribute`
            acoustic attribute
        """
        return self.attribute.acoustic

    @property
    def base_annotation(self):
        """
        Returns
        -------
        :class:`~polyglotdb.graph.attributes.AnnotationAttribute`
            base annotation
        """
        return self.attribute.base_annotation

    @property
    def with_alias(self):
        """
        Returns
        -------
        with_alias : str
            the alias of a `~polyglotdb.graph.attributes.AnnotationAttribute` object
        """
        return self.attribute.with_alias

    @property
    def with_aliases(self):
        """
        Returns
        -------
        with_aliases : str
            the with strings of a `~polyglotdb.graph.attributes.AnnotationAttribute` object
        """
        return self.attribute.with_aliases

    @property
    def output_alias(self):
        """
        Returns
        -------
        output_label : str
            the output label
        """
        if self.output_label is None:
            if self.attribute is not None:
                name = self.attribute.label
            else:
                name = 'all'
            return '{}_{}'.format(self.__class__.__name__.lower(), name)
        else:
            return self.output_label

    def aliased_for_output(self):
        """
        Returns
        -------
        str
            output alias cypher string
        """
        prop = self.for_cypher()
        output = self.output_alias
        return '{} AS {}'.format(prop, output)

    @property
    def collapsing(self):
        """
        Returns
        -------
        False if there is a PathAttribute, True otherwise
        """
        if self.attribute is not None and self.attribute.collapsing:
            return False
        return True

    def column_name(self, label):
        """
        sets output label

        Parameters
        ----------
        label : str
            the label to set

        Returns
        -------
        self
        """
        self.output_label = label
        return self

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        if not self.collapsing:
            return self.collection_templates[self.function].format(
                property=self.attribute.for_cypher())
        elif self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            element = '*'
        return self.template.format(function=self.function,
                                    property=element)


class Average(AggregateFunction):
    function = 'avg'


class Count(AggregateFunction):
    function = 'count'


class Sum(AggregateFunction):
    function = 'sum'


class Stdev(AggregateFunction):
    function = 'stdev'


class Max(AggregateFunction):
    function = 'max'


class Min(AggregateFunction):
    function = 'min'


class Quantile(AggregateFunction):
    function = 'percentileDisc'
    template = '{function}({property}, {percentile})'

    def __init__(self, attribute, percentile=0.5):
        self.attribute = attribute
        self.percentile = percentile
        self.output_label = None

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        if self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            raise (AttributeError)
        return self.template.format(function=self.function,
                                    percentile=self.percentile,
                                    property=element)


class Median(Quantile):
    def __init__(self, attribute):
        Quantile.__init__(self, attribute, 0.5)


class InterquartileRange(AggregateFunction):
    template = 'percentileDisc({property}, 0.75) - percentileDisc({property}, 0.25)'

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        if self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            raise (AttributeError)
        return self.template.format(property=element)
