
from .elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement)

from .attributes import AggregateAttribute, PathAttribute

class AggregateFunction(object):
    function = ''
    template = '{function}({property})'
    collection_templates = {'sum': 'reduce(count = 0, n in {property} | count + n)',
                            'avg': 'reduce(count = 0, n in {property} | count + n) / toFloat(size({property}))',
                            'count': 'size({property})'}
    def __init__(self, attribute = None):
        self.attribute = attribute
        self.output_label = None

    def __hash__(self):
        return hash((self.function, self.attribute))

    @property
    def base_annotation(self):
        return self.attribute.base_annotation

    @property
    def with_alias(self):
        return self.attribute.with_alias

    @property
    def with_aliases(self):
        return self.attribute.with_aliases

    @property
    def annotation(self):
        return self.attribute.annotation

    @property
    def output_alias(self):
        if self.output_label is None:
            if self.attribute is not None:
                name = self.attribute.label
            else:
                name = 'all'
            return '{}_{}'.format(self.__class__.__name__.lower(), name)
        else:
            return self.output_label


    def aliased_for_output(self):
        prop = self.for_cypher()
        output = self.output_alias
        return '{} AS {}'.format(prop, output)

    @property
    def collapsing(self):
        if self.attribute is not None and isinstance(self.attribute, PathAttribute):
            return False
        return True

    def column_name(self, label):
        self.output_label = label
        return self

    def for_cypher(self):
        if not self.collapsing:
            return self.collection_templates[self.function].format(
                                property = self.attribute.for_cypher())
        elif self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            element = '*'
        return self.template.format(function = self.function,
                                property = element)

    def __eq__(self, other):
        return EqualClauseElement(AggregateAttribute(self), other)

    def __ne__(self, other):
        return NotEqualClauseElement(AggregateAttribute(self), other)

    def __gt__(self, other):
        return GtClauseElement(AggregateAttribute(self), other)

    def __ge__(self, other):
        return GteClauseElement(AggregateAttribute(self), other)

    def __lt__(self, other):
        return LtClauseElement(AggregateAttribute(self), other)

    def __le__(self, other):
        return LteClauseElement(AggregateAttribute(self), other)

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
    def __init__(self, attribute, percentile = 0.5):
        self.attribute = attribute
        self.percentile = percentile
        self.output_label = None

    def for_cypher(self):
        if self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            raise(AttributeError)
        return self.template.format(function = self.function,
                                percentile = self.percentile,
                                property = element)

class Median(Quantile):
    def __init__(self, attribute):
        Quantile.__init__(self, attribute, 0.5)

class InterquartileRange(AggregateFunction):
    template = 'percentileDisc({property}, 0.75) - percentileDisc({property}, 0.25)'

    def for_cypher(self):
        if self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            raise(AttributeError)
        return self.template.format(property = element)
