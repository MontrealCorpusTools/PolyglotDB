
class AggregateFunction(object):
    function = ''
    def __init__(self, key):
        self.key = key

    def for_cypher(self):
        if self.key == 'duration':
            element = 'e.time - b.time'
        elif self.key == 'begin':
            element = 'b.time'
        elif self.key == 'end':
            element = 'e.time'
        else:
            element = self.key
        if self.key != '*':
            template = '{function}({property}) AS {readable_function}_{name}'
        else:
            template = '{function}({property}) AS {readable_function}_all'
        return template.format(function = self.function,
                                readable_function = self.__class__.__name__.lower(),
                                property = element,
                                name = self.key)

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
