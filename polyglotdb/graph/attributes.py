
from .helper import key_for_cypher

from .query import GraphQuery

from .elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement,
                        InClauseElement, ContainsClauseElement, RegexClauseElement,
                        RightAlignedClauseElement, LeftAlignedClauseElement)

class Attribute(object):
    """
    Class for information about the attributes of annotations in a graph
    query

    Parameters
    ----------
    annotation : AnnotationAttribute
        Annotation that this attribute refers to
    label : str
        Label of the attribute

    Attributes
    ----------
    annotation : AnnotationAttribute
        Annotation that this attribute refers to
    label : str
        Label of the attribute
    output_label : str or None
        User-specified label to use in query results
    """
    def __init__(self, annotation, label):
        self.annotation = annotation
        self.label = label
        self.output_label = None

    def __hash__(self):
        return hash((self.annotation, self.label))

    def for_cypher(self):
        if self.label == 'begin':
            b_node = self.annotation.begin_alias
            return '{}.time'.format(b_node)
        elif self.label == 'end':
            e_node = self.annotation.end_alias
            return '{}.time'.format(e_node)
        elif self.label == 'duration':
            b_node = self.annotation.begin_alias
            e_node = self.annotation.end_alias
            return '{}.time - {}.time'.format(e_node, b_node)
        elif self.label == 'discourse':
            b_node = self.annotation.begin_alias
            return '{}.discourse'.format(b_node)
        return '{}.{}'.format(self.annotation.alias, key_for_cypher(self.label))

    @property
    def alias(self):
        return '{}_{}'.format(self.annotation.alias, self.label)

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
        try:
            if self.label == 'begin' and other.label == 'begin':
                return LeftAlignedClauseElement(self.annotation, other.annotation)
            elif self.label == 'end' and other.label == 'end':
                return RightAlignedClauseElement(self.annotation, other.annotation)
        except AttributeError:
            pass
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
                t.append(getattr(x, self.label))
        else:
            t = other
        return InClauseElement(self, t)

    def regex(self, pattern):
        return RegexClauseElement(self, pattern)

class AnnotationAttribute(Attribute):
    """
    Class for annotations referenced in graph queries

    Parameters
    ----------
    type : str
        Annotation type
    pos : int
        Position in the query, defaults to 0

    Attributes
    ----------
    type : str
        Annotation type
    pos : int
        Position in the query
    previous : AnnotationAttribute
        Returns the Annotation of the same type with the previous position
    following : AnnotationAttribute
        Returns the Annotation of the same type with the following position
    """
    begin_template = '{}_b{}'
    end_template = '{}_e{}'
    def __init__(self, type, pos = 0):
        self.type = type
        self.pos = pos

    def __hash__(self):
        return hash((self.type, self.pos))

    def __repr__(self):
        return '<AnnotationAttribute object with \'{}\' type and {} position'.format(self.type, self.pos)

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

    def right_aligned(self, other):
        return RightAlignedClauseElement(self, other)

    def left_aligned(self, other):
        return LeftAlignedClauseElement(self, other)

    def __getattr__(self, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return AnnotationAttribute(self.type, pos)
        else:
            return Attribute(self, key)
