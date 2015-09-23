
from .helper import key_for_cypher

from .query import GraphQuery

from .elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement,
                        InClauseElement, ContainsClauseElement)

class Attribute(object):
    def __init__(self, annotation, label):
        self.annotation = annotation
        self.name = label

        self.output_label = None

    def __hash__(self):
        return hash((self.annotation, self.name))

    def for_cypher(self):
        if self.name == 'begin':
            b_node = self.annotation.begin_alias
            return '{}.time'.format(b_node)
        elif self.name == 'end':
            e_node = self.annotation.end_alias
            return '{}.time'.format(e_node)
        elif self.name == 'duration':
            b_node = self.annotation.begin_alias
            e_node = self.annotation.end_alias
            return '{}.time - {}.time'.format(e_node, b_node)
        elif self.name == 'discourse':
            b_node = self.annotation.begin_alias
            return '{}.discourse'.format(b_node)
        return '{}.{}'.format(self.annotation.alias, key_for_cypher(self.name))

    @property
    def alias(self):
        return '{}_{}'.format(self.annotation.alias, self.name)

    def aliased_for_cypher(self):
        return '{} AS {}'.format(self.for_cypher(), self.alias)

    def aliased_for_output(self):
        if self.output_label is not None:
            a = self.output_label
        else:
            a = self.alias
        return '{} AS {}'.format(self.for_cypher(), a)

    @property
    def output_alias(self):
        if self.output_label is not None:
            return self.output_label
        return self.alias

    def column_name(self, label):
        self.output_label = label
        return self

    def __eq__(self, other):
        return EqualClauseElement(self, other)

    def __ne__(self, other):
        return NotEqualClauseElement(self, other)

    def __gt__(self, other):
        return GtClauseElement(self, other)

    def __gte__(self, other):
        return GteClauseElement(self, other)

    def __lt__(self, other):
        return LtClauseElement(self, other)

    def __lte__(self, other):
        return LteClauseElement(self, other)

    def in_(self, other):
        if isinstance(other, GraphQuery):
            results = other.all()
            t = []
            for x in results:
                t.append(getattr(x, other.to_find.alias).properties[self.name])
        else:
            t = other
        return InClauseElement(self, t)

class AnnotationAttribute(Attribute):
    begin_template = '{}_b{}'
    end_template = '{}_e{}'
    def __init__(self, type, pos = 0):
        self.type = type
        self.pos = pos

    def __hash__(self):
        return hash((self.type, self.pos))

    @property
    def rel_alias(self):
        if self.pos == 0:
            return 'r_{t}:{t}'.format(t=self.type)
        elif self.pos < 0:
            return 'prevr{p}_{t}:{t}'.format(t=self.type, p = -1 * self.pos)
        elif self.pos > 0:
            return 'follr{p}_{t}:{t}'.format(t=self.type, p = self.pos)

    @property
    def alias(self):
        if self.pos == 0:
            return 'r_{t}'.format(t=self.type)
        elif self.pos < 0:
            return 'prevr{p}_{t}'.format(t=self.type, p = -1 * self.pos)
        elif self.pos > 0:
            return 'follr{p}_{t}'.format(t=self.type, p = self.pos)

    @property
    def begin_alias(self):
        if self.pos == 0:
            return self.begin_template.format(self.type, self.pos)
        elif self.pos > 0:
            return self.end_template.format(self.type, self.pos - 1)
        elif self.pos < 0:
            return self.begin_template.format(self.type, -1 * self.pos)

    @property
    def end_alias(self):
        if self.pos == 0:
            return self.end_template.format(self.type, self.pos)
        elif self.pos > 0:
            return self.end_template.format(self.type, self.pos)
        elif self.pos < 0:
            return self.begin_template.format(self.type, -1 * (self.pos + 1))

    def __getattr__(self, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return AnnotationAttribute(self.type, pos)
        else:
            return Attribute(self, key)
