
from .helper import key_for_cypher, value_for_cypher

class ClauseElement(object):
    sign = ''
    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    def for_cypher(self):
        try:
            value = self.value.for_cypher()
        except AttributeError:
            value = value_for_cypher(self.value)
        return "{} {} {}".format(self.attribute.for_cypher(),
                                self.sign,
                                value)

class EqualClauseElement(ClauseElement):
    sign = '='

class GtClauseElement(ClauseElement):
    sign = '>'

class GteClauseElement(ClauseElement):
    sign = '>='

class LtClauseElement(ClauseElement):
    sign = '<'

class LteClauseElement(ClauseElement):
    sign = '<='

class NotEqualClauseElement(ClauseElement):
    sign = '<>'

class InClauseElement(ClauseElement):
    sign = 'IN'

class RegexClauseElement(ClauseElement):
    sign = '=~'

class ContainsClauseElement(ClauseElement):
    def for_cypher(self):
        return "{} in extract(x in {}| x.{})".format(value_for_cypher(self.value),
                                                self.attribute.annotation.alias,
                                                key_for_cypher(self.attribute.label))
