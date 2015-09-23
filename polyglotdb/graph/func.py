

class AggregateFunction(object):
    function = ''
    def __init__(self, attribute = None):
        self.attribute = attribute

    def for_cypher(self):
        template = '{function}({property}) AS {readable_function}_{name}'
        if self.attribute is not None:
            element = self.attribute.for_cypher()
            name = self.attribute.name
        else:
            element = '*'
            name = 'all'
        return template.format(function = self.function,
                                readable_function = self.__class__.__name__.lower(),
                                property = element,
                                name = name)

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
