
from .helper import key_for_cypher

from .query import GraphQuery

from .elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement,
                        InClauseElement, ContainsClauseElement)

class MetaAnnotation(type):
    def __getattr__(cls, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = -1
            else:
                pos = 1
            return AnnotationAttribute(key, pos)
        else:
            return Attribute(key, 0)

class Attribute(object):
    def __init__(self, label, pos = 0):
        self.name = label
        self.pos = pos

    def for_cypher(self):
        if self.name == 'begin':
            return 'b.time'
        elif self.name == 'end':
            return 'e.time'
        if self.pos == 0:
            return 'r.{}'.format(key_for_cypher(self.name))
        if self.pos < 0:
            temp = 'prevr{}.{}'
        elif self.pos > 0:
            temp = 'follr{}.{}'
        return temp.format(self.pos,key_for_cypher(self.name))

    def aliased_for_cypher(self):
        if self.name == 'begin':
            return 'b.time AS begin'
        elif self.name == 'end':
            return 'e.time AS end'
        if self.pos == 0:
            return 'r.{} as {}'.format(key_for_cypher(self.name), self.name)
        if self.pos < 0:
            temp = 'prevr{}.{} AS previous_{}'
        elif self.pos > 0:
            temp = 'follr{}.{} AS following_{}'
        return temp.format(self.pos,key_for_cypher(self.name), self.name)


    def __eq__(self, other):
        return EqualClauseElement(self.name, other, self.pos)

    def __neq__(self, other):
        return NotEqualClauseElement(self.name, other, self.pos)

    def __gt__(self, other):
        return GtClauseElement(self.name, other, self.pos)

    def __gte__(self, other):
        return GteClauseElement(self.name, other, self.pos)

    def __lt__(self, other):
        return LtClauseElement(self.name, other, self.pos)

    def __lte__(self, other):
        return LteClauseElement(self.name, other, self.pos)

    def in_(self, other):
        if isinstance(other, GraphQuery):
            other = other.all()
            t = []
            for x in other:
                try:
                    t.append(x.r.properties[self.name])
                except AttributeError:
                    t.append(x)
        else:
            t = other
        return InClauseElement(self.name, t, self.pos)

class AnnotationAttribute(Attribute):
    def __init__(self, key, pos = 0):
        self.key = key
        self.pos = pos

    def __getattr__(self, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return AnnotationAttribute(key, pos)
        else:
            return Attribute(key, self.pos)
