import json
from uuid import uuid1
from py2neo import Node, Relationship

def value_for_cypher(value):
    if isinstance(value, str):
        return "'{}'".format(value)
    if isinstance(value, list):
        return json.dumps(value)
    else:
        return "{}".format(value)

def key_for_cypher(key):
    if ' ' in key:
        return "`{}`".format(key)
    return key

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
        if other.__class__.__name__ == 'Query': #Avoid circular imports
            other = other.all()
            t = []
            for x in other:
                print(x)
                try:
                    t.append(x.r.properties[self.name])
                except AttributeError:
                    t.append(x)
        else:
            t = other
        print(t)
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


class Annotation(Relationship, metaclass = MetaAnnotation):
    def __init__(self, begin_node, end_node, type, label):
        Relationship.__init__(self, begin_node, type, end_node)
        self.properties['label'] = label
        self.properties['id'] = str(uuid1())


class Anchor(Node):
    def __init__(self, **kwargs):
        Node.__init__(self, uuid1(), **kwargs)
