
from ..helper import key_for_cypher

from ..elements import (EqualClauseElement, GtClauseElement, GteClauseElement,
                        LtClauseElement, LteClauseElement, NotEqualClauseElement,
                        InClauseElement, NotInClauseElement, ContainsClauseElement, RegexClauseElement,
                        RightAlignedClauseElement, LeftAlignedClauseElement,
                        NotRightAlignedClauseElement, NotLeftAlignedClauseElement,
                        SubsetClauseElement, NotSubsetClauseElement,
                        NullClauseElement, NotNullClauseElement,
                        FollowsClauseElement, PrecedesClauseElement)

from ...exceptions import SubsetError

special_attributes = ['duration', 'count', 'rate', 'position', 'type_subset',
                    'token_subset']

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
    def __init__(self, annotation, label, type):
        self.annotation = annotation
        self.label = label
        self.output_label = None
        self.type = type
        self.acoustic = False

    def __hash__(self):
        return hash((self.annotation, self.label))

    def __str__(self):
        return '{}.{}'.format(self.annotation.alias, self.label)

    def __repr__(self):
        return '<Attribute \'{}\'>'.format(str(self))

    def for_cypher(self):
        """Returns annotation duration or annotation type if applicable, otherwise annotation name and label """
        if self.label == 'duration':
            return '{a}.end - {a}.begin'.format(a = self.annotation.alias)
        if self.type:
            return '{}.{}'.format(self.annotation.type_alias, key_for_cypher(self.label))
        return '{}.{}'.format(self.annotation.alias, key_for_cypher(self.label))

    def for_filter(self):
        return self.for_cypher()

    def for_column(self):
        return self.for_cypher()

    @property
    def base_annotation(self):
        """ returns the annotation """
        return self.annotation

    @base_annotation.setter
    def base_annotation(self, value):
        """ sets the annotation to value """
        self.annotation = value

    @property
    def alias(self):
        """ Removes '`' from annotation, concatenates annotation alias and label"""
        return '`{}_{}`'.format(self.annotation.alias.replace('`',''), self.label)

    def aliased_for_cypher(self):
        """
        creates cypher string to use in db

        Returns
        -------
        string
            string for db
        """
        return '{} AS {}'.format(self.for_cypher(), self.alias)

    def aliased_for_output(self):
        """
        creates cypher string for output

        Returns
        -------
        string
            string for output
        """
        return '{} AS {}'.format(self.for_cypher(), self.output_alias)

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
    def with_alias(self):
        """
        returns type_alias if there is one
        alias otherwise
        """
        if self.type:
            return self.annotation.type_alias
        else:
            return self.annotation.alias

    def column_name(self, label):
        """
        sets a column name to label
        """
        self.output_label = label
        return self

    def __eq__(self, other):
        try:
            if self.label == 'begin' and other.label == 'begin':
                print(other.annotation.depth)
                return LeftAlignedClauseElement(self.annotation, other.annotation)
            elif self.label == 'end' and other.label == 'end':
                return RightAlignedClauseElement(self.annotation, other.annotation)
            elif self.label in ['token_subset', 'type_subset']:
                return SubsetClauseElement(self, other)
        except AttributeError:
            pass
        if other is None:
            return NullClauseElement(self, other)
        return EqualClauseElement(self, other)

    def __ne__(self, other):
        try:
            if self.label == 'begin' and other.label == 'begin':
                return NotLeftAlignedClauseElement(self.annotation, other.annotation)
            elif self.label == 'end' and other.label == 'end':
                return NotRightAlignedClauseElement(self.annotation, other.annotation)
            elif self.label in ['token_subset', 'type_subset']:
                return NotSubsetClauseElement(self, other)
        except AttributeError:
            pass
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
    previous : :class:`~polyglotdb.graph.attributes.AnnotationAttribute`
        Returns the Annotation of the same type with the previous position
    following : :class:`~polyglotdb.graph.attributes.AnnotationAttribute`
        Returns the Annotation of the same type with the following position
    """
    has_subquery = False
    alias_prefix = ''
    template = '''({token_alias})-[:is_a]->({type_alias})'''
    #template = '''({token_alias})'''
    begin_template = '{}_{}_begin'
    end_template = '{}_{}_end'
    alias_template = '{prefix}node_{t}'
    rel_type_template = 'r_{t}'

    def __init__(self, type, pos = 0, corpus = None, hierarchy = None):
        self.type = type
        self.pos = pos
        self.corpus = corpus
        self.hierarchy = hierarchy
        self.subset_token_labels = []
        self.subset_type_labels = []

    def __hash__(self):
        return hash((self.key, self.pos))

    def __eq__(self, other):
        if not isinstance(other, AnnotationAttribute):
            return False
        if self.type != other.type:
            return False
        if self.pos != other.pos:
            return False
        return True

    def __str__(self):
        return '{}_{}'.format(self.key, self.pos)

    def __repr__(self):
        return '<AnnotationAttribute object with \'{}\' type and {} position>'.format(self.type, self.pos)

    def for_match(self):
        """ sets 'token_alias' and 'type_alias'  keyword arguments for an annotation """
        kwargs = {}
        kwargs['token_alias'] = self.define_alias
        kwargs['type_alias'] = self.define_type_alias
        return self.template.format(**kwargs)

    def subset_type(self, *args):
        """ adds each item in args to the hierarchy type_labels"""
        if self.hierarchy is not None:
            for a in args:
                if not self.hierarchy.has_type_subset(self.type, a):
                    raise(SubsetError('{} is not a subset of {} types.'.format(a, self.type)))
        self.subset_type_labels.extend(args)
        return self

    def subset_token(self, *args):

        """ adds each item in args to the hierarchy token_labels"""
        if self.hierarchy is not None:
            for a in args:
                if not self.hierarchy.has_token_subset(self.type, a):
                    raise(SubsetError('{} is not a subset of {} tokens.'.format(a, self.type)))
        self.subset_token_labels.extend(args)
        return self

    @property
    def define_type_alias(self):
        """ Returns a cypher string for getting all type_labels"""
        label_string = ':{}_type'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        if self.subset_type_labels:
            label_string += ':' + ':'.join(map(key_for_cypher, self.subset_type_labels))
        return '{}{}'.format(self.type_alias, label_string)

    @property
    def define_alias(self):
        """ Returns a cypher string for getting all token_labels"""
        label_string = ':{}:speech'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        if self.subset_token_labels:
            label_string += ':' + ':'.join(map(key_for_cypher, self.subset_token_labels))
        return '{}{}'.format(self.alias, label_string)

    @property
    def type_alias(self):
        """ Returns a cypher formatted string of type alias"""
        return key_for_cypher('type_'+self.alias.replace('`', ''))

    @property
    def alias(self):
        """Returns a cypher formatted string of keys and prefixes"""
        pre = self.alias_prefix
        if self.pos < 0:
            pre += 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre += 'foll_{}_'.format(self.pos)
        return key_for_cypher(self.alias_template.format(t=self.key, prefix = pre))

    @property
    def with_alias(self):
        """ Returns alias """
        return self.alias

    @property
    def withs(self):
        """ Returns a list of alias and type_alias """
        return [self.alias, self.type_alias]

    def precedes(self, other_annotation):
        return PrecedesClauseElement(self, other_annotation)

    def follows(self, other_annotation):
        return FollowsClauseElement(self, other_annotation)

    def __getattr__(self, key):
        if key == 'annotation':
            raise(AttributeError('Annotations do not have annotation attributes.'))
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return AnnotationAttribute(self.type, pos, corpus = self.corpus, hierarchy = self.hierarchy)
        elif key == 'follows_pause':
            from .pause import FollowsPauseAttribute
            return FollowsPauseAttribute(self)
        elif key == 'precedes_pause':
            from .pause import PrecedesPauseAttribute
            return PrecedesPauseAttribute(self)
        elif key == 'speaker':
            from .speaker import SpeakerAnnotation
            return SpeakerAnnotation(self, corpus = self.corpus)
        elif key == 'discourse':
            from .discourse import DiscourseAnnotation
            return DiscourseAnnotation(self, corpus = self.corpus)
        elif key == 'pause':
            from .pause import PauseAnnotation
            return PauseAnnotation(self.pos, corpus = self.corpus, hierarchy = self.hierarchy)
        elif key == 'pitch':
            from .acoustic import PitchAttribute
            return PitchAttribute(self)
        elif key == 'formants':
            from .acoustic import FormantAttribute
            return FormantAttribute(self)
        elif self.hierarchy is not None and key in self.hierarchy.contained_by(self.type):
            from .hierarchical import HierarchicalAnnotation
            return HierarchicalAnnotation(key, self, corpus = self.corpus, hierarchy = self.hierarchy)
        elif self.hierarchy is not None and key in self.hierarchy.contains(self.type):
            from .path import SubPathAnnotation
            return SubPathAnnotation(self, AnnotationAttribute(key, self.pos, corpus = self.corpus))
        elif self.hierarchy is not None \
                and self.type in self.hierarchy.subannotations \
                and key in self.hierarchy.subannotations[self.type]:
            from .subannotation import SubAnnotation
            return SubAnnotation(self, AnnotationAttribute(key, self.pos, corpus = self.corpus))
        else:
            if self.hierarchy is None or key in special_attributes:
                type = False
            else:
                if self.hierarchy.has_type_property(self.type, key):
                    type = True
                elif self.hierarchy.has_token_property(self.type, key):
                    type = False
                else:
                    raise(AttributeError('The \'{}\' annotation types do not have a \'{}\' property.'.format(self.type, key)))

            return Attribute(self, key, type)

    @property
    def key(self):
        """
        Returns
        -------
        key : str
            has the object type followed by all token labels and then all type labels
        """
        key = self.type
        if self.subset_token_labels:
            key += '_' + '_'.join(self.subset_token_labels)
        if self.subset_type_labels:
            key += '_' + '_'.join(self.subset_type_labels)
        return key
