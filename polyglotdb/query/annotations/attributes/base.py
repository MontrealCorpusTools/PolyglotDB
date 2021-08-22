from ...base.helper import key_for_cypher
from ....exceptions import AnnotationAttributeError, SubsetError

from ..elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement,
                        InClauseElement, NotInClauseElement, RegexClauseElement,
                        RightAlignedClauseElement, LeftAlignedClauseElement,
                        NotRightAlignedClauseElement, NotLeftAlignedClauseElement,
                        SubsetClauseElement, NotSubsetClauseElement,
                        NullClauseElement, NotNullClauseElement,
                        FollowsClauseElement, PrecedesClauseElement)

from ...base import NodeAttribute, Node, CollectionNode, CollectionAttribute

special_attributes = ['duration', 'count', 'rate', 'position', 'subset']


class AnnotationAttribute(NodeAttribute):
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
    collapsing = False

    def __init__(self, annotation, label):
        super(AnnotationAttribute, self).__init__(annotation, label)
        self.acoustic = False

    def __hash__(self):
        return hash((self.node, self.label))

    def __repr__(self):
        return '<AnnotationAttribute \'{}\'>'.format(str(self))

    def requires_type(self):
        if self.node.hierarchy is None or self.label in special_attributes:
            return False
        return not self.node.hierarchy.has_token_property(self.node.node_type, self.label)

    def for_cypher(self, type=False):
        """Returns annotation duration or annotation type if applicable, otherwise annotation name and label """
        if self.label == 'duration':
            return '{a}.end - {a}.begin'.format(a=self.node.alias)
        if type or self.requires_type():
            return '{}.{}'.format(self.node.type_alias, key_for_cypher(self.label))
        return '{}.{}'.format(self.node.alias, key_for_cypher(self.label))

    @property
    def with_alias(self):
        """
        returns type_alias if there is one
        alias otherwise
        """
        if self.requires_type():
            return self.node.type_alias
        else:
            return self.node.alias

    def __eq__(self, other):
        try:
            if self.label == 'begin' and other.label == 'begin':
                return LeftAlignedClauseElement(self.node, other.node)
            elif self.label == 'end' and other.label == 'end':
                return RightAlignedClauseElement(self.node, other.node)
        except AttributeError:
            pass
        if self.label == 'subset':
            return SubsetClauseElement(self, other)
        if other is None:
            return NullClauseElement(self, other)
        return EqualClauseElement(self, other)

    def __ne__(self, other):
        try:
            if self.label == 'begin' and other.label == 'begin':
                return NotLeftAlignedClauseElement(self.node, other.node)
            elif self.label == 'end' and other.label == 'end':
                return NotRightAlignedClauseElement(self.node, other.node)
        except AttributeError:
            pass
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

    def aliased_for_output(self, type=False):
        """
        creates cypher string for output

        Returns
        -------
        string
            string for output
        """
        return '{} AS {}'.format(self.for_cypher(type), self.output_alias_for_cypher)

    def for_type_filter(self):
        return self.for_cypher(type=True)


class AnnotationNode(Node):
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
    previous : :class:`~polyglotdb.graph.attributes.AnnotationAttribute`
        Returns the Annotation of the same type with the previous position
    following : :class:`~polyglotdb.graph.attributes.AnnotationAttribute`
        Returns the Annotation of the same type with the following position
    """
    match_template = '''({token_alias})-[:is_a]->({type_alias})'''
    # template = '''({token_alias})'''
    begin_template = '{}_{}_begin'
    end_template = '{}_{}_end'
    alias_template = 'node_{t}'

    def __init__(self, node_type, corpus=None, hierarchy=None):
        super(AnnotationNode, self).__init__(node_type, corpus=corpus, hierarchy=hierarchy)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, AnnotationNode):
            return False
        if self.key != other.key:
            return False
        return True

    def __str__(self):
        return '{}_0'.format(self.key)

    def __repr__(self):
        return '<AnnotationNode object with \'{}\' type>'.format(self.node_type)

    def for_match(self):
        """ sets 'token_alias' and 'type_alias'  keyword arguments for an annotation """
        kwargs = {'token_alias': self.define_alias,
                  'type_alias': self.define_type_alias}
        return self.match_template.format(**kwargs)

    def filter_by_subset(self, *args):
        """ adds each item in args to the hierarchy type_labels"""
        if self.hierarchy is not None:
            for a in args:
                if not self.hierarchy.has_type_subset(self.node_type, a) and not self.hierarchy.has_token_subset(
                        self.node_type, a):
                    raise (SubsetError('{} is not a subset of {} types or tokens.'.format(a, self.node_type)))
        self.subset_labels = sorted(set(self.subset_labels + list(args)))
        return self

    @property
    def define_type_alias(self):
        """ Returns a cypher string for getting all type_labels"""
        label_string = ':{}_type'.format(self.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        if self.subset_labels:
            subset_type_labels = [x for x in self.subset_labels if self.hierarchy.has_type_subset(self.node_type, x)]
            if subset_type_labels:
                label_string += ':' + ':'.join(map(key_for_cypher, subset_type_labels))
        return '{}{}'.format(self.type_alias, label_string)

    @property
    def define_alias(self):
        """ Returns a cypher string for getting all token_labels"""
        label_string = ':{}:speech'.format(self.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        if self.subset_labels:
            subset_token_labels = [x for x in self.subset_labels if self.hierarchy.has_token_subset(self.node_type, x)]
            if subset_token_labels:
                label_string += ':' + ':'.join(map(key_for_cypher, subset_token_labels))
        return '{}{}'.format(self.alias, label_string)

    @property
    def type_alias(self):
        """ Returns a cypher formatted string of type alias"""
        return key_for_cypher('type_' + self.alias.replace('`', ''))

    @property
    def alias(self):
        """Returns a cypher formatted string of keys and prefixes"""
        return key_for_cypher(self.alias_template.format(t=self.key))

    @property
    def with_alias(self):
        """ Returns alias """
        return self.alias

    @property
    def labels_alias(self):
        """ Returns alias """
        return 'labels({}) as {}'.format(self.alias, key_for_cypher(self.alias + '_labels'))

    @property
    def withs(self):
        """ Returns a list of alias and type_alias """
        return [self.alias, self.type_alias, self.labels_alias]

    def precedes(self, other_annotation):
        return PrecedesClauseElement(self, other_annotation)

    def follows(self, other_annotation):
        return FollowsClauseElement(self, other_annotation)

    def __getattr__(self, key):
        if key == 'current':
            return self
        elif key in ['previous', 'following']:
            from .precedence import PreviousAnnotation, FollowingAnnotation
            if key == 'previous':
                return PreviousAnnotation(self, -1)
            else:
                return FollowingAnnotation(self, 1)
        elif key in ['previous_pause', 'following_pause']:
            from .pause import FollowingPauseAnnotation, PreviousPauseAnnotation
            node = self
            if self.node_type != self.hierarchy.word_name:
                node = getattr(self, self.hierarchy.word_name)
            if key == 'previous_pause':
                return PreviousPauseAnnotation(node)
            else:
                return FollowingPauseAnnotation(node)
        elif key.startswith('previous'):
            p, key = key.split('_', 1)
            p = self.previous
            return getattr(p, key)
        elif key.startswith('following'):
            p, key = key.split('_', 1)
            f = self.following
            return getattr(f, key)
        elif key == 'follows_pause':
            from .pause import FollowsPauseAttribute
            return FollowsPauseAttribute(self)
        elif key == 'precedes_pause':
            from .pause import PrecedesPauseAttribute
            return PrecedesPauseAttribute(self)
        elif key == 'speaker':
            from .speaker import SpeakerAnnotation
            return SpeakerAnnotation(self)
        elif key == 'discourse':
            from .discourse import DiscourseAnnotation
            return DiscourseAnnotation(self)
        elif key in self.hierarchy.acoustics:
            from .acoustic import AcousticAttribute
            return AcousticAttribute(self, key)
        elif self.hierarchy is not None and key in self.hierarchy.get_higher_types(self.node_type):
            from .hierarchical import HierarchicalAnnotation
            types = self.hierarchy.get_higher_types(self.node_type)
            prev_node = self
            cur_node = None
            for t in types:
                higher_node = AnnotationNode(t, corpus=self.corpus, hierarchy=self.hierarchy)
                cur_node = HierarchicalAnnotation(prev_node, higher_node)
                prev_node = cur_node
                if t == key:
                    break
            return cur_node
        elif self.hierarchy is not None and key in self.hierarchy.get_lower_types(self.node_type):
            from .path import SubPathAnnotation
            return SubPathAnnotation(self, AnnotationNode(key, corpus=self.corpus))
        elif self.hierarchy is not None \
                and self.node_type in self.hierarchy.subannotations \
                and key in self.hierarchy.subannotations[self.node_type]:
            from .subannotation import SubAnnotation
            return SubAnnotation(self, AnnotationNode(key, corpus=self.corpus))
        else:
            if key not in special_attributes and self.hierarchy is not None and not self.hierarchy.has_token_property(
                    self.node_type, key) and not self.hierarchy.has_type_property(self.node_type, key):
                properties = [x[0] for x in
                              self.hierarchy.type_properties[self.node_type] | self.hierarchy.token_properties[
                                  self.node_type]]
                raise AnnotationAttributeError(
                    'The \'{}\' annotation types do not have a \'{}\' property (available: {}).'.format(self.node_type,
                                                                                                        key, ', '.join(
                            properties)))
            return AnnotationAttribute(self, key)


class AnnotationCollectionNode(CollectionNode):
    def with_statement(self):
        """ """
        return ', '.join(['collect(n) as {a}'.format(a=self.collection_alias),
                          'collect(t) as {a}'.format(a=self.collection_type_alias)])

    @property
    def withs(self):
        withs = [self.collection_alias, self.collection_type_alias]
        return withs


class AnnotationCollectionAttribute(CollectionAttribute):
    pass
