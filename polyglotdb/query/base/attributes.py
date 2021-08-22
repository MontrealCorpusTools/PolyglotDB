from .helper import key_for_cypher
from .elements import (EqualClauseElement, NotEqualClauseElement, SubsetClauseElement,
                       NotSubsetClauseElement, NullClauseElement, NotNullClauseElement,
                       InClauseElement, NotInClauseElement, GtClauseElement, GteClauseElement,
                       LtClauseElement, LteClauseElement, RegexClauseElement)


class NodeAttribute(object):
    has_subquery = False
    acoustic = False

    def __init__(self, node, label):
        self.node = node
        self.label = label
        self.output_label = None

    def __hash__(self):
        return hash((self.node, self.label))

    def __str__(self):
        return '{}.{}'.format(self.node, self.label)

    def __repr__(self):
        return '<NodeAttribute \'{}\'>'.format(str(self))

    def for_cypher(self):
        return '{}.{}'.format(self.node.alias, key_for_cypher(self.label))

    def for_json(self):
        return [[x for x in self.node.for_json()] + [self.label], self.output_label]

    def for_filter(self):
        return self.for_cypher()

    def for_column(self):
        return self.for_cypher()

    def value_type(self):
        a_type = self.node.node_type
        if a_type == 'Speaker':
            for name, t in self.node.hierarchy.speaker_properties:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        elif a_type == 'Discourse':
            for name, t in self.node.hierarchy.discourse_properties:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t

        elif self.node.hierarchy.has_token_property(a_type, self.label):
            for name, t in self.node.hierarchy.token_properties[a_type]:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        elif self.node.hierarchy.has_type_property(a_type, self.label):
            for name, t in self.node.hierarchy.type_properties[a_type]:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        elif self.node.hierarchy.has_subannotation_property(a_type, self.label):
            for name, t in self.node.hierarchy.subannotation_properties[a_type]:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        raise ValueError('Property type "{}" not found for "{}".'.format(self.label, a_type))

    def coerce_value(self, value):
        if value is None:
            return value
        t = self.value_type()
        if t is None:
            return None
        if isinstance(value, list):
            return [t(x) for x in value]
        return t(value)

    @property
    def alias(self):
        """ Removes '`' from annotation, concatenates annotation alias and label"""
        return '{}_{}'.format(self.node.alias.replace('`', ''), self.label)

    @property
    def alias_for_cypher(self):
        return '`{}_{}`'.format(self.node.alias.replace('`', ''), self.label)

    def aliased_for_cypher(self):
        """
        creates cypher string to use in db

        Returns
        -------
        string
            string for db
        """
        return '{} AS {}'.format(self.for_cypher(), self.alias_for_cypher)

    def for_return(self):
        return self.for_cypher()

    def aliased_for_output(self):
        """
        creates cypher string for output

        Returns
        -------
        string
            string for output
        """
        return '{} AS {}'.format(self.for_return(), self.output_alias_for_cypher)

    @property
    def output_alias(self):
        """
        returns output_label if there is one
        return alias otherwise
        """
        if self.output_label is not None:
            return self.output_label
        return self.alias

    @property
    def output_alias_for_cypher(self):
        """
        returns output_label if there is one
        return alias otherwise
        """
        if self.output_label is not None:
            return self.output_label
        return self.alias_for_cypher

    @property
    def with_alias(self):
        """
        returns type_alias if there is one
        alias otherwise
        """
        return self.node.alias

    def column_name(self, label):
        """
        sets a column name to label
        """
        self.output_label = label
        return self

    def __eq__(self, other):
        if self.label == 'subset':
            return SubsetClauseElement(self, other)
        if other is None:
            return NullClauseElement(self, other)
        return EqualClauseElement(self, other)

    def __ne__(self, other):
        if self.label == 'subset':
            return NotSubsetClauseElement(self, other)
        if other is None:
            return NotNullClauseElement(self, other)
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
        """
        Checks if the parameter other has a 'cypher' element
        executes the query if it does and appends the relevant results
        or appends parameter other

        Parameters
        ----------
        other : list
            attribute will be checked against elements in this list
        Returns
        -------
        string
            clause for asserting membership in a filter

        """
        if hasattr(other, 'cypher'):
            results = other.all()
            t = []
            for x in results:
                t.append(getattr(x, self.label))
        else:
            t = other
        return InClauseElement(self, t)

    def not_in_(self, other):
        """
        Checks if the parameter other has a 'cypher' element
        executes the query if it does and appends the relevant results
        or appends parameter other

        Parameters
        ----------
        other : list
            attribute will be checked against elements in this list
        Returns
        -------
        string
            clause for asserting non-membership in a filter
        """
        if hasattr(other, 'cypher'):
            results = other.all()
            t = []
            for x in results:
                t.append(getattr(x, self.label))
        else:
            t = other
        return NotInClauseElement(self, t)

    def regex(self, pattern):
        """ Returns a clause for filtering based on regular expressions."""
        return RegexClauseElement(self, pattern)

    @property
    def nodes(self):
        return self.node.nodes

    cache_alias = alias


class CollectionAttribute(NodeAttribute):
    collapsing = True
    acoustic = False
    filter_template = '{alias}.{property}'
    return_template = '[n in {alias}|n.{property}]'

    def __repr__(self):
        return '<CollectionAttribute \'{}\'>'.format(str(self))

    def value_type(self):
        n = self.node.collected_node
        a_type = n.node_type
        if a_type == 'Speaker':
            for name, t in self.node.hierarchy.speaker_properties:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        elif a_type == 'Discourse':
            for name, t in self.node.hierarchy.discourse_properties:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t

        elif self.node.hierarchy.has_token_property(a_type, self.label):
            for name, t in self.node.hierarchy.token_properties[a_type]:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        elif self.node.hierarchy.has_type_property(a_type, self.label):
            for name, t in self.node.hierarchy.type_properties[a_type]:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        elif self.node.hierarchy.has_subannotation_property(a_type, self.label):
            for name, t in self.node.hierarchy.subannotation_properties[a_type]:
                if name == self.label:
                    if t == type(None) or t is None:
                        return None
                    return t
        raise ValueError('Property type "{}" not found for "{}".'.format(self.label, a_type))

    def for_cypher(self):
        return self.for_return()

    def for_filter(self):
        return self.filter_template.format(alias=self.node.collection_alias, property=self.label)

    def for_return(self):
        return self.return_template.format(alias=self.node.collection_alias, property=self.label)

    @property
    def with_aliases(self):
        """Returns annotation withs list """
        return self.node.withs

    @property
    def with_alias(self):
        """returns annotation path_alias """
        return self.node.collection_alias

    @property
    def cache_alias(self):
        return self.node.anchor_node.alias


class Node(object):
    non_optional = True
    has_subquery = False
    alias_template = 'node_{t}'
    match_template = '({alias})'

    def __init__(self, node_type, corpus=None, hierarchy=None):
        self.node_type = node_type
        self.corpus = corpus
        self.hierarchy = hierarchy
        self.subset_labels = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        if self.node_type != other.node_type:
            return False
        if self.corpus != other.corpus:
            return False
        if self.subset_labels != other.subset_labels:
            return False
        return True

    def __hash__(self):
        return hash(self.key)

    def __str__(self):
        return self.key

    def __repr__(self):
        return '<Node of {} in {} corpus'.format(self.node_type, self.corpus)

    def __getattr__(self, key):
        return NodeAttribute(self, key)

    @property
    def key(self):
        key = self.node_type
        if self.subset_labels:
            key += '_' + '_'.join(self.subset_labels)
        return key

    def for_json(self):
        return [self.node_type]

    def for_match(self):
        return self.match_template.format(alias=self.define_alias)

    @property
    def alias(self):
        return key_for_cypher(self.alias_template.format(t=self.key))

    @property
    def define_alias(self):
        label_string = ':{}'.format(self.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        if self.subset_labels:
            label_string += ':' + ':'.join(map(key_for_cypher, self.subset_labels))
        return '{}{}'.format(self.alias, label_string)

    def filter_by_subset(self, *args):
        """ adds each item in args to the hierarchy type_labels"""
        self.subset_labels = sorted(set(self.subset_labels + list(args)))
        return self

    @property
    def with_alias(self):
        return self.alias

    @property
    def withs(self):
        return [self.alias]

    @property
    def nodes(self):
        return [self]


class CollectionNode(object):
    has_subquery = True
    non_optional = False
    subquery_match_template = '({anchor_node_alias})-->({def_collection_alias})'
    subquery_order_by_template = ''
    subquery_template = '''{optional}MATCH {for_match}
        {where_string}
        WITH {input_with_string}, {with_pre_collection}
        {sub_query}
        {order_by}
        WITH {output_with_string}'''
    collect_template = 'collect({a}) as {a}'

    def __init__(self, anchor_node, collected_node):
        self.anchor_node = anchor_node
        self.collected_node = collected_node

    def subquery(self, withs, filters=None, optional=False):
        input_with = ', '.join(withs)
        new_withs = withs - {self.collection_alias}
        output_with = ', '.join(new_withs) + ', ' + self.with_statement()
        where_string = ''
        if filters is not None:
            relevant = []
            for c in filters:
                if c.involves(self):
                    relevant.append(c.for_cypher())
            if relevant:
                where_string = 'WHERE ' + '\nAND '.join(relevant)
        for_match = self.subquery_match_template.format(anchor_node_alias=self.anchor_node.alias,
                                                        def_collection_alias=self.def_collection_alias)
        order_by = self.subquery_order_by_template
        kwargs = {'for_match': for_match,
                  'where_string': where_string,
                  'input_with_string': input_with,
                  'order_by': order_by,
                  'sub_query': '',
                  'optional': '',
                  'with_pre_collection': self.with_pre_collection,
                  'output_with_string': output_with}
        if optional:
            kwargs['optional']= 'OPTIONAL '
        return self.subquery_template.format(**kwargs)

    @property
    def with_pre_collection(self):
        return self.collection_alias

    def __eq__(self, other):
        if not isinstance(other, CollectionNode):
            return False
        if self.anchor_node != other.anchor_node:
            return False
        if self.collected_node != other.collected_node:
            return False
        return True

    @property
    def nodes(self):
        return [self] + self.anchor_node.nodes + self.collected_node.nodes

    @property
    def hierarchy(self):
        return self.anchor_node.hierarchy

    @property
    def corpus(self):
        return self.anchor_node.corpus

    @property
    def node_type(self):
        return self.anchor_node.node_type

    def __str__(self):
        return '{}.{}'.format(self.anchor_node, self.collected_node)

    def __repr__(self):
        return '<CollectionNode of {} under {}'.format(str(self.collected_node), str(self.anchor_node))

    def __hash__(self):
        return hash((self.anchor_node, self.collected_node))

    @property
    def withs(self):
        withs = [self.collection_alias]
        return withs

    def with_statement(self):
        withs = [self.collect_template.format(a=self.collection_alias)
                 ]
        return ', '.join(withs)

    @property
    def def_collection_alias(self):
        label_string = ':{}'.format(self.collected_node.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.collected_node.corpus))
        if self.collected_node.subset_labels:
            label_string += ':' + ':'.join(map(key_for_cypher, self.collected_node.subset_labels))
        return '{}{}'.format(self.collection_alias, label_string)

    @property
    def collection_alias(self):
        return key_for_cypher('{}_in_{}'.format(self.collected_node.alias, self.anchor_node.alias))

    alias = collection_alias

    def filter_by_subset(self, *args):
        self.collected_node = self.collected_node.filter_by_subset(*args)
        return self

    def __getattr__(self, key):
        return CollectionAttribute(self, key)
