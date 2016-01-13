
from .elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement)

from .attributes import AggregateAttribute, PathAttribute

class AggregateFunction(object):
    function = ''
    template = '{function}({property}) AS {output_name}'
    collection_templates = {'sum': 'reduce(count = 0, n in {property} | count + n) AS {output_name}',
                            'avg': 'reduce(count = 0, n in {property} | count + n) / toFloat(size({property})) AS {output_name}',
                            'count': 'size({property}) AS {output_name}'}
    def __init__(self, attribute = None):
        self.attribute = attribute
        self.output_label = None

    def aliased_for_output(self):
        if self.output_label is None:
            if self.attribute is not None:
                name = self.attribute.label
            else:
                name = 'all'
            return '{}_{}'.format(self.__class__.__name__.lower(), name)
        else:
            return self.output_label

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
                                property = self.attribute.for_cypher(),
                                output_name = self.aliased_for_output())
        elif self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            element = '*'
        return self.template.format(function = self.function,
                                property = element,
                                output_name = self.aliased_for_output())

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
    template = '{function}({property}, {percentile}) AS {output_name}'
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
                                output_name = self.aliased_for_output(),
                                property = element)

class Median(Quantile):
    def __init__(self, attribute):
        Quantile.__init__(self, attribute, 0.5)

class InterquartileRange(AggregateFunction):
    template = 'percentileDisc({property}, 0.75) - percentileDisc({property}, 0.25) AS {output_name}'

    def for_cypher(self):
        if self.attribute is not None:
            element = self.attribute.for_cypher()
        else:
            raise(AttributeError)
        return self.template.format(output_name = self.aliased_for_output(),
                                property = element)
