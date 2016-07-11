
from .helper import key_for_cypher, value_for_cypher

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

    def cypher_value_string(self):
        """
        Create a Cypher parameter for the value of the clause.
        """
        return '{`%s%s`}' % (self.value_alias_prefix.replace('`',''), self.attribute.alias.replace('`',''))

    @property
    def annotations(self):
        """
        Get all annotations involved in the clause.
        """
        annotations = [self.attribute.base_annotation]
        try:
            annotations.append(self.value.base_annotation)
        except AttributeError:
            pass
        return annotations

    @property
    def attributes(self):
        """
        Get all attributes involved in the clause.
        """
        attributes = [self.attribute]
        if hasattr(self.value, 'annotation'):
            attributes.append(self.value)
        return attributes

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        try:
            value = self.value.for_cypher()
        except AttributeError:
            value = self.cypher_value_string()
        return self.template.format(self.attribute.for_cypher(),
                                self.sign,
                                value)

class PrecedenceClauseElement(ClauseElement):
    value_alias_prefix = ''
    template = "({})-[:precedes*]->({{id: {}}})"
    def __init__(self, annotation, other_annotation):
        self.annotation = annotation
        self.value = other_annotation.id

    @property
    def annotations(self):
        """
        Get all annotations involved in the clause.
        """
        annotations = [self.annotation]
        return annotations

    @property
    def attributes(self):
        return []

    def cypher_value_string(self):
        """
        Create a Cypher parameter for the value of the clause.
        """
        return '{`%s%s`}' % (self.value_alias_prefix.replace('`',''), self.annotation.alias.replace('`',''))

    def for_cypher(self):

        key = self.annotation.alias

        return self.template.format(node_alias = key, id_string = self.cypher_value_string())

class PrecedesClauseElement(PrecedenceClauseElement):
    value_alias_prefix = 'precedes_'
    template = "({node_alias})-[:precedes*]->({{id: {id_string}}})"

class FollowsClauseElement(PrecedenceClauseElement):
    value_alias_prefix = 'follows_'
    template = "({{id: {id_string}}})-[:precedes*]->({node_alias})"

class SubsetClauseElement(ClauseElement):
    template = "{}:{}"
    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        value = key_for_cypher(self.value)
        if self.attribute.label == 'token_subset':
            key = self.attribute.annotation.alias
        elif self.attribute.label == 'type_subset':
            key = self.attribute.annotation.type_alias
        return self.template.format(key,
                                value)

class NotSubsetClauseElement(ClauseElement):
    template = "NOT {}:{}"
    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        value = key_for_cypher(self.value)
        if self.attribute.label == 'token_subset':
            key = self.attribute.annotation.alias
        elif self.attribute.label == 'type_subset':
            key = self.attribute.annotation.type_alias
        return self.template.format(key,
                                value)

class NullClauseElement(ClauseElement):
    template = '{} is null'
    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        return self.template.format(self.attribute.for_cypher())

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

class ContainsClauseElement(ClauseElement):
    """
    Clause for filtering based on hierarchical relations.
    """
    sign = 'contains'
    template = '''({alias})<-[:contained_by]-({token})-[:is_a]->({type} {{{label}: {value}}})'''
    def for_cypher(self):
        kwargs = {'alias':self.attribute.annotation.alias,
                'value':value_for_cypher(self.value),
                'label': key_for_cypher(self.attribute.label),
                'type': ':{}_type'.format(self.attribute.annotation.type),
                'token': ':{}'.format(self.attribute.annotation.type)}
        return self.template.format(**kwargs)

class AlignmentClauseElement(ClauseElement):
    """
    Base class for filtering based on alignment.
    """
    template = "{first}.label = {second}.label"
    side = ''
    def __init__(self, first, second):
        from .attributes import HierarchicalAnnotation
        self.first = first

        if not isinstance(first, HierarchicalAnnotation) and not isinstance(second, HierarchicalAnnotation):
            second = getattr(self.first, second.type)
        self.second = second
        self.depth = 1
        lower = self.first.type
        higher = self.second.type
        if lower not in self.first.hierarchy.contains(higher):
            lower, higher = higher, lower
        t = self.first.hierarchy.get_higher_types(lower)
        for i in t:
            if i == higher:
                break
            self.depth += 1

    def __hash__(self):
        return hash((self.first, self.template, self.second))

    @property
    def annotations(self):
        """
        Returns
        -------
        first and second annotations
        """
        return [self.first, self.second]

    @property
    def attributes(self):
        """
        Returns
        -------
        the ID of the first annotation
        """
        return [self.first.id]

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        kwargs = {'second_node_alias': self.second.alias,
                'first_node_alias': self.first.alias}
        if self.depth != 1:
            kwargs['depth'] = '*' + str(self.depth)
        else:
            kwargs['depth'] = ''
        return self.template.format(**kwargs)

class RightAlignedClauseElement(AlignmentClauseElement):
    """
    Clause for filtering based on right alignment.
    """
    template = '''not ({first_node_alias})-[:precedes]->()-[:contained_by{depth}]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by{depth}]->({second_node_alias})'''

class LeftAlignedClauseElement(AlignmentClauseElement):
    """
    Clause for filtering based on left alignment.
    """
    template = '''not ({first_node_alias})<-[:precedes]-()-[:contained_by{depth}]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by{depth}]->({second_node_alias})'''

class NotRightAlignedClauseElement(RightAlignedClauseElement):
    """
    Clause for filtering based on not being right aligned.
    """
    template = '''({first_node_alias})-[:precedes]->()-[:contained_by{depth}]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by{depth}]->({second_node_alias})'''

class NotLeftAlignedClauseElement(LeftAlignedClauseElement):
    """
    Clause for filtering based on not being left aligned.
    """
    template = '''({first_node_alias})<-[:precedes]-()-[:contained_by{depth}]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by{depth}]->({second_node_alias})'''

class ComplexClause(object):
    type_string = ''
    def __init__(self, *args):
        self.clauses = args
        self.add_prefix(self.type_string)

    @property
    def annotations(self):
        """
        Get all annotations involved in the clause.
        """
        annotations = []
        for a in self.clauses:
            annotations.extend(a.annotations)
        return annotations

    @property
    def attributes(self):
        """
        Get all attributes involved in the clause.
        """
        attributes = []
        for a in self.clauses:
            attributes.extend(a.attributes)
        return attributes

    def add_prefix(self, prefix):
        """
        Adds a prefix to a clause

        Parameters
        ----------
        prefix : str
            the prefix to add
        """
        for i, c in enumerate(self.clauses):
            if isinstance(c, ComplexClause):
                c.add_prefix(prefix+ str(i))
            else:
                try:
                    c.value_alias_prefix += prefix + str(i)
                except AttributeError:
                    pass

    def generate_params(self):
        """
        Generates dictionary of parameters of ComplexClause

        Returns
        -------
        params : dict
            a dictionary of parameters
        """
        from .attributes import Attribute
        params = {}
        for c in self.clauses:
            if isinstance(c, ComplexClause):
                params.update(c.generate_params())
            else:
                try:
                    if not isinstance(c.value, Attribute):
                        params[c.cypher_value_string()[1:-1].replace('`','')] = c.value
                except AttributeError:
                    pass
        return params

class or_(ComplexClause):
    type_string = 'or_'

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        temp = ' OR '.join(x.for_cypher() for x in self.clauses)
        temp = "(" + temp + ")"
        return temp

class and_(ComplexClause):
    type_string = 'and_'
    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        temp = ' AND '.join(x.for_cypher() for x in self.clauses)
        temp = "(" + temp + ")"
        return temp

