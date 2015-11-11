
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
    def base_annotation(self):
        return self.annotation

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

    @property
    def is_type_attribute(self):
        if self.label in type_attributes:
            return True
        return False

    @property
    def with_alias(self):
        if self.label in type_attributes:
            return self.annotation.type_alias
        else:
            return self.annotation.alias

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
    has_subquery = False
    alias_prefix = ''
    begin_template = '{}_{}_begin'
    end_template = '{}_{}_end'
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
        label_string = ':{}:speech'.format(self.type)
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
        pre = self.alias_prefix + 'type_'
        if self.pos < 0:
            pre += 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre += 'foll_{}_'.format(self.pos)
        return self.alias_template.format(t=self.type, prefix = pre)

    @property
    def alias(self):
        pre = self.alias_prefix
        if self.pos < 0:
            pre += 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre += 'foll_{}_'.format(self.pos)
        return self.alias_template.format(t=self.type, prefix = pre)

    @property
    def with_alias(self):
        return self.alias

    @property
    def path_alias(self):
        return 'path_'+self.alias

    @property
    def begin_alias(self):
        if self.pos == 0:
            return self.begin_template.format(self.type, self.pos)
        elif self.pos > 0:
            return self.begin_template.format(self.type, self.pos)
        elif self.pos < 0:
            return self.begin_template.format(self.type, -1 * self.pos)

    @property
    def end_alias(self):
        if self.pos == 0:
            return self.end_template.format(self.type, self.pos)
        elif self.pos > 0:
            return self.end_template.format(self.type, self.pos)
        elif self.pos < 0:
            return self.end_template.format(self.type, -1 * (self.pos))

    def right_aligned(self, other):
        return RightAlignedClauseElement(self, other)

    def left_aligned(self, other):
        return LeftAlignedClauseElement(self, other)

    def __getattr__(self, key):
        if key == 'annotation':
            raise(AttributeError('Annotations do not have annotation attributes.'))
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return AnnotationAttribute(self.type, pos, corpus = self.corpus, contains = self.contains)
        elif key == 'pause':
            return PauseAnnotation(pos, corpus = self.corpus, contains = self.contains)
        elif self.contains is not None and key in self.contains:
            return SubPathAnnotation(self, AnnotationAttribute(key, self.pos, corpus = self.corpus))

        else:
            return Attribute(self, key)

    @property
    def key(self):
        return self.type

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

class PathAnnotation(AnnotationAttribute):
    has_subquery = True
    path_prefix = 'path_'
    with_type_template = 'collect({type_alias}) AS {type}'
    with_times_template = 'extract(n in filter(n in nodes({path_alias}) where n.time is not null)| n.time) as {path_times_alias}'

    subquery_template = '''UNWIND nodes({path_alias}) as n
        MATCH ()-[:r_{key}]->(n)-[:is_a]->({path_type_alias})
        WITH {output_with_string}'''

    def type_subquery(self, withs):
        input_with = ', '.join(withs)
        output_with = input_with + ', ' + self.with_type()
        return self.generate_type_subquery(output_with, input_with)

    def times_subquery(self, withs):
        input_with = ', '.join(withs)
        output_with = input_with + ', ' + self.with_times()
        return '''WITH {}'''.format(output_with)

    def generate_type_subquery(self, output_with_string, input_with_string):
        return self.subquery_template.format(path_alias = self.path_alias,
                        output_with_string = output_with_string,
                        key = self.key,
                        path_type_alias = self.define_type_alias)

    @property
    def path_alias(self):
        return self.path_prefix + self.alias

    @property
    def type_alias(self):
        return self.path_alias + '_type'

    @property
    def path_type_alias(self):
        return self.path_prefix + self.type_alias

    @property
    def times_alias(self):
        return self.path_alias + '_times'

    def with_times(self):
        return self.with_times_template.format(path_alias = self.path_alias, path_times_alias = self.times_alias)

    def with_type(self):
        return self.with_type_template.format(type_alias = self.type_alias, type = self.path_type_alias)

    @property
    def key(self):
        return 'pause'

    def __getattr__(self, key):
        if key == 'annotation':
            raise(AttributeError('Annotations cannot have annotations.'))
        return PathAttribute(self, key)

class SubPathAnnotation(PathAnnotation):
    subquery_template = '''MATCH p = shortestPath(({begin_alias})-[:r_{sub_type}*]->({end_alias}))
        WITH {input_with_string}, p
        UNWIND nodes(p) as n
        MATCH (n)-[:is_a]->({path_type_alias})
        WITH {output_with_string}'''

    def __init__(self, super_annotation, sub_annotation):
        self.annotation = super_annotation
        self.sub = sub_annotation

    def generate_type_subquery(self, output_with_string, input_with_string):
        return self.subquery_template.format(begin_alias = self.annotation.begin_alias, end_alias = self.annotation.end_alias,
                        input_with_string = input_with_string, output_with_string = output_with_string, sub_type = self.sub.type,
                        path_type_alias = self.type_alias)

    def __hash__(self):
        return hash((self.annotation, self.sub))

    @property
    def alias(self):
        return self.sub.alias

    @property
    def end_alias(self):
        return self.annotation.end_alias

    @property
    def begin_alias(self):
        return self.annotation.begin_alias

    @property
    def path_type_alias(self):
        return 'path_'+self.sub.type_alias

    @property
    def key(self):
        return self.sub.type



class PathAttribute(Attribute):
    type_return_template = 'extract(n in {alias}|n.{property})'
    count_return_template = 'reduce(count = 0, n in {alias} | count + 1)'
    rate_return_template = 'reduce(count = 0, n in {alias} | count + 1) / ({end_alias}.time - {begin_alias}.time)'

    @property
    def base_annotation(self):
        if isinstance(self.annotation, SubPathAnnotation):
            return self.annotation.annotation
        else:
            return self.annotation

    def for_cypher(self):
        if self.label in type_attributes:
            return self.type_return_template.format(alias = self.annotation.path_type_alias, property = self.label)

        if self.annotation.pos >= 0:
            begpos = 0
            endpos = -2
        else:
            begpos = 1
            endpos = -1
        if self.label == 'begin':
            return '{}[{}]'.format(self.annotation.times_alias, begpos)
        elif self.label == 'end':
            return '{}[{}]'.format(self.annotation.times_alias, endpos)
        elif self.label == 'duration':
            return '{alias}[{endpos}] - {alias}[{begpos}]'.format(alias = self.annotation.times_alias, endpos = endpos, begpos = begpos)
        elif self.label == 'count':
            return self.count_return_template.format(alias = self.annotation.path_type_alias)
        elif self.label == 'rate':
            return self.rate_return_template.format(alias = self.annotation.path_type_alias,
                                end_alias = self.annotation.end_alias,
                                begin_alias = self.annotation.begin_alias)

    @property
    def is_type_attribute(self):
        if self.label in type_attributes + ['rate', 'count']:
            return True
        return False

    @property
    def with_alias(self):
        if self.label in type_attributes + ['rate', 'count']:
            print(self.label, self.annotation.path_type_alias)
            return self.annotation.path_type_alias
        elif self.label in ['duration', 'begin', 'end']:
            return self.annotation.times_alias

class PauseAnnotation(AnnotationAttribute):
    def __init__(self, pos = 0, corpus = None, contains = None):
        self.type = 'word'
        self.pos = pos
        self.corpus = corpus
        self.contains = contains
        self.discourse_label = None

    @property
    def define_alias(self):
        label_string = ':{}:pause'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        if self.discourse_label is not None:
            label_string += ':{}'.format(self.discourse)
        return '{}{}'.format(self.alias, label_string)

    def __getattr__(self, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return PathAnnotation(self.type, pos, corpus = self.corpus, contains = self.contains)

        return Attribute(self, key)

    @property
    def key(self):
        return 'pause'

