
from .helper import key_for_cypher, value_for_cypher

class ClauseElement(object):
    sign = ''
    def __init__(self, key, value, pos):
        self.key = key
        self.value = value
        self.pos = pos

    def __str__(self):
        return "{}:'{}'".format(self.key, self.value)

    def for_cypher(self, item_name):
        if self.key == 'type':
            return "type({}) {} {}".format(item_name, self.sign, value_for_cypher(self.value))
        elif self.key == 'begin':
            return "b.time {} {}".format(self.sign, value_for_cypher(self.value))
        elif self.key == 'end':
            return "e.time {} {}".format(self.sign, value_for_cypher(self.value))
        return "{}.{} {} {}".format(item_name,
                                key_for_cypher(self.key),
                                self.sign,
                                value_for_cypher(self.value))

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


class ContainsClauseElement(EqualClauseElement):
    def for_cypher(self, item_name):
        return "{} in extract(x in {}| x.{})".format(value_for_cypher(self.value),
                                                item_name,
                                                key_for_cypher(self.key))
