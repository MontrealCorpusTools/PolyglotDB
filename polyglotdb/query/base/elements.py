from .helper import key_for_cypher

from ...exceptions import NodeAttributeError


class ClauseElement(object):
    """
    Base class for filter elements that will be translated to Cypher.
    """
    sign = ''
    template = "{} {} {}"

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value
        self.value_alias_prefix = ''

    def __repr__(self):
        return '<ClauseElement \'{}\'>'.format(self.for_cypher())

    def __hash__(self):
        return hash((self.attribute, self.sign, self.value))

    def for_json(self):
        from .attributes import NodeAttribute

        if isinstance(self.value, NodeAttribute):
            value = self.value.for_json()
        else:
            value = self.value
        return [self.attribute.for_json(), self.sign, value]

    def cypher_value_string(self):
        """
        Create a Cypher parameter for the value of the clause.
        """
        return '$`%s%s`' % (self.value_alias_prefix.replace('`', ''), self.attribute.alias.replace('`', ''))

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        try:
            value = self.value.for_filter()
        except AttributeError:
            value = self.cypher_value_string()
        return self.template.format(self.attribute.for_filter(),
                                    self.sign,
                                    value)

    def for_type_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        try:
            value = self.value.for_type_filter()
        except AttributeError:
            value = self.cypher_value_string()
        return self.template.format(self.attribute.for_type_filter(),
                                    self.sign,
                                    value)

    @property
    def nodes(self):
        n = self.attribute.node
        ns = n.nodes
        try:
            ns.append(self.value.node)
        except AttributeError:
            pass
        return ns

    @property
    def attributes(self):
        """
        Get all attributes involved in the clause.
        """
        attributes = [self.attribute]
        if hasattr(self.value, 'node'):
            attributes.append(self.value)
        return attributes

    def involves(self, annotation):
        to_match = 'alias'
        if annotation.has_subquery:
            to_match = 'collection_alias'
        try:
            if getattr(self.attribute.node, to_match, None) == getattr(annotation, to_match):
                return True
        except NodeAttributeError:
            pass
        try:
            if getattr(self.value.node, to_match, None) == getattr(annotation, to_match):
                return True
        except (AttributeError, NodeAttributeError):
            pass
        return False

    @property
    def in_subquery(self):
        for n in self.nodes:
            if n.has_subquery:
                return True
        return False

class NullClauseElement(ClauseElement):
    template = '{} is null'

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        return self.template.format(self.attribute.for_cypher())

    @property
    def nodes(self):
        return [self.attribute.node]


class NotNullClauseElement(NullClauseElement):
    template = '{} is not null'


class EqualClauseElement(ClauseElement):
    """
    Clause for asserting equality in a filter.
    """
    sign = '='


class GtClauseElement(ClauseElement):
    """
    Clause for asserting greater than in a filter.
    """
    sign = '>'


class GteClauseElement(ClauseElement):
    """
    Clause for asserting greater than or equal in a filter.
    """
    sign = '>='


class LtClauseElement(ClauseElement):
    """
    Clause for asserting less than in a filter.
    """
    sign = '<'


class LteClauseElement(ClauseElement):
    """
    Clause for asserting less than or equal in a filter.
    """
    sign = '<='


class NotEqualClauseElement(ClauseElement):
    """
    Clause for asserting not equal in a filter.
    """
    sign = '<>'


class InClauseElement(ClauseElement):
    """
    Clause for asserting membership in a filter.
    """
    sign = 'IN'


class NotInClauseElement(InClauseElement):
    """
    Clause for asserting membership in a filter.
    """
    template = "NOT {} {} {}"


class RegexClauseElement(ClauseElement):
    """
    Clause for filtering based on regular expressions.
    """
    sign = '=~'


class SubsetClauseElement(ClauseElement):
    template = "{}:{}"

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        value = key_for_cypher(self.value)
        key = self.attribute.node.alias
        return self.template.format(key,
                                    value)

    @property
    def nodes(self):
        return [self.attribute.node]


class NotSubsetClauseElement(SubsetClauseElement):
    template = "NOT {}:{}"
