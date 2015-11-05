
from .helper import key_for_cypher, anchor_attributes, type_attributes

from .elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement,
                        InClauseElement, ContainsClauseElement, RegexClauseElement,
                        RightAlignedClauseElement, LeftAlignedClauseElement,
                        NotRightAlignedClauseElement, NotLeftAlignedClauseElement)

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

    def __str__(self):
        return '{}.{}'.format(self.annotation.alias, self.label)

    def __repr__(self):
        return '<Attribute \'{}\'>'.format(str(self))

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
        if self.label not in type_attributes:
            return '{}.{}'.format(self.annotation.alias, key_for_cypher(self.label))
        return '{}.{}'.format(self.annotation.type_alias, key_for_cypher(self.label))

    @property
    def alias(self):
        return '{}_{}'.format(self.annotation.alias, self.label)

    def aliased_for_cypher(self):
        return '{} AS {}'.format(self.for_cypher(), self.alias)

    def aliased_for_output(self):
        return '{} AS {}'.format(self.for_cypher(), self.output_alias)

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
        try:
            if self.label == 'begin' and other.label == 'begin':
                return NotLeftAlignedClauseElement(self.annotation, other.annotation)
            elif self.label == 'end' and other.label == 'end':
                return NotRightAlignedClauseElement(self.annotation, other.annotation)
        except AttributeError:
            pass
        return NotEqualClauseElement(self, other)

    def __gt__(self, other):
        return GtClauseElement(self, other)

    def __ge__(self, other):
        return GteClauseElement(self, other)

    def __lt__(self, other):
        return LtClauseElement(self, other)

    def __le__(self, other):
        return LteClauseElement(self, other)

    def in_(self, other):
        if hasattr(other, 'cypher'):
            results = other.all()
            t = []
            for x in results:
                t.append(getattr(x, self.label))
        else:
            t = other
        return InClauseElement(self, t)

    def regex(self, pattern):
        return RegexClauseElement(self, pattern)

class AggregateAttribute(Attribute):
    def __init__(self, aggregate):
        self.aggregate = aggregate

    @property
    def alias(self):
        return '{}_{}_{}'.format(self.annotation.alias, self.label, self.aggregate.function)

    @property
    def annotation(self):
        return self.aggregate.attribute.annotation

    @property
    def label(self):
        return self.aggregate.attribute.label

    @property
    def output_label(self):
        return self.aggregate.aliased_for_output()

    def for_with(self):
        return self.aggregate.for_cypher()

    def for_cypher(self):
        return self.output_label

class PathAttribute(Attribute):
    match_template = '({alias})<-[:contained_by]-(:{sub_type}:{corpus})-[:is_a]->({sub_type_alias})'
    with_template = 'collect({sub_type_alias}) AS {type}'
    return_template = 'extract(n in {type}|n.label)'
    def __init__(self, super_annotation, sub_annotation):
        self.annotation = super_annotation
        self.sub = sub_annotation
        self.output_label = None

    @property
    def label(self):
        return self.sub.type

    def for_subquery(self, withs):
        input_with = ', '.join(withs)
        output_with = input_with + ', ' + self.for_with()
        template = '''MATCH p = ({begin_alias})-[:r_{sub_type}*]->({end_alias})
        WITH {input_with_string}, p
        UNWIND nodes(p) as n
        MATCH (n)-[:is_a]->({sub_type_alias})
        WITH {output_with_string}'''
        return template.format(begin_alias = self.annotation.begin_alias, end_alias = self.annotation.end_alias,
                        input_with_string = input_with, output_with_string = output_with, sub_type = self.sub.type,
                        sub_type_alias = self.sub.define_type_alias)

    def for_match(self):
        return self.match_template.format(alias = self.annotation.alias, sub_type = self.sub.type, corpus = self.sub.corpus, sub_type_alias = self.sub.define_type_alias)

    def for_with(self):
        return self.with_template.format(sub_type_alias = self.sub.type_alias, type = self.sub.type)

    @property
    def output_alias(self):
        if self.output_label is not None:
            return self.output_label
        return self.sub.type + 's'

    def for_cypher(self):
        return self.return_template.format(type = self.sub.type)


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
    alias_template = '{prefix}node_{t}'
    rel_type_template = 'r_{t}'
    def __init__(self, type, pos = 0, corpus = None, contains = None):
        self.type = type
        self.pos = pos
        self.corpus = corpus
        self.contains = contains
        self.discourse_label = None

    def __hash__(self):
        return hash((self.type, self.pos))

    def __repr__(self):
        return '<AnnotationAttribute object with \'{}\' type and {} position'.format(self.type, self.pos)

    @property
    def rel_alias(self):
        return '-[:r_{t}]->({alias}:{t})-[:r_{t}]->'.format(t=self.type, alias = self.alias)

    @property
    def rel_type_alias(self):
        return self.rel_type_template.format(t=self.type)

    @property
    def define_type_alias(self):
        label_string = ':{}_type'.format(self.type)
        return '{}{}'.format(self.type_alias, label_string)

    @property
    def define_alias(self):
        label_string = ':{}'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        if self.discourse_label is not None:
            label_string += ':{}'.format(self.discourse)
        return '{}{}'.format(self.alias, label_string)

    @property
    def define_begin_alias(self):
        label_string = ':Anchor'
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        if self.discourse_label is not None:
            label_string += ':{}'.format(self.discourse)
        return '{}{}'.format(self.begin_alias, label_string)

    @property
    def define_end_alias(self):
        label_string = ':Anchor'
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        if self.discourse_label is not None:
            label_string += ':{}'.format(self.discourse)
        return '{}{}'.format(self.end_alias, label_string)

    @property
    def type_alias(self):
        pre = 'type_'
        if self.pos < 0:
            pre += 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre += 'foll_{}_'.format(self.pos)
        return self.alias_template.format(t=self.type, prefix = pre)

    @property
    def alias(self):
        if self.pos == 0:
            pre = ''
        elif self.pos < 0:
            pre = 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre = 'foll_{}_'.format(self.pos)
        return self.alias_template.format(t=self.type, prefix = pre)

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
            return AnnotationAttribute(self.type, pos, corpus = self.corpus, contains = self.contains)
        elif self.contains is not None and key in self.contains:
            return PathAttribute(self, AnnotationAttribute(key, self.pos, corpus = self.corpus))

        else:
            return Attribute(self, key)
