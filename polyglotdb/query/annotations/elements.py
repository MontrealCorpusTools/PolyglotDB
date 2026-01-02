from polyglotdb.query.base.elements import ClauseElement
from polyglotdb.query.base.elements import EqualClauseElement as BaseEqualClauseElement
from polyglotdb.query.base.elements import GtClauseElement as BaseGtClauseElement
from polyglotdb.query.base.elements import GteClauseElement as BaseGteClauseElement
from polyglotdb.query.base.elements import InClauseElement as BaseInClauseElement
from polyglotdb.query.base.elements import LtClauseElement as BaseLtClauseElement
from polyglotdb.query.base.elements import LteClauseElement as BaseLteClauseElement
from polyglotdb.query.base.elements import NotEqualClauseElement as BaseNotEqualClauseElement
from polyglotdb.query.base.elements import NotInClauseElement as BaseNotInClauseElement
from polyglotdb.query.base.elements import NotNullClauseElement as BaseNotNullClauseElement
from polyglotdb.query.base.elements import NullClauseElement as BaseNullClauseElement
from polyglotdb.query.base.elements import RegexClauseElement as BaseRegexClauseElement
from polyglotdb.query.base.helper import key_for_cypher, value_for_cypher


class AnnotationClauseElement(ClauseElement):
    """
    Base class for filter elements that will be translated to Cypher.
    """

    def __repr__(self):
        return "<AnnotationClauseElement '{}'>".format(self.for_cypher())


class PrecedenceClauseElement(AnnotationClauseElement):
    value_alias_prefix = ""
    template = "({})-[:precedes*]->({{id: {}}})"

    def __init__(self, annotation, other_annotation):
        self.node = annotation
        self.value = other_annotation.id

    @property
    def nodes(self):
        """
        Get all annotations involved in the clause.
        """
        return self.node.nodes

    @property
    def attributes(self):
        return []

    def cypher_value_string(self):
        """
        Create a Cypher parameter for the value of the clause.
        """
        return "$`%s%s`" % (
            self.value_alias_prefix.replace("`", ""),
            self.node.alias.replace("`", ""),
        )

    def for_cypher(self):
        key = self.node.alias

        return self.template.format(node_alias=key, id_string=self.cypher_value_string())

    def is_matrix(self):
        from .attributes import SubPathAnnotation

        if isinstance(self.node, SubPathAnnotation):
            return False
        return True

    def involves(self, annotation):
        from .attributes import SubPathAnnotation

        to_match = "alias"
        if isinstance(annotation, SubPathAnnotation):
            to_match = "collection_alias"
        if getattr(self.node, to_match, None) == getattr(annotation, to_match):
            return True
        return False


class PrecedesClauseElement(PrecedenceClauseElement):
    value_alias_prefix = "precedes_"
    template = "({node_alias})-[:precedes*]->({{id: {id_string}}})"


class FollowsClauseElement(PrecedenceClauseElement):
    value_alias_prefix = "follows_"
    template = "({{id: {id_string}}})-[:precedes*]->({node_alias})"


class NotPrecedesClauseElement(PrecedenceClauseElement):
    value_alias_prefix = "precedes_"
    template = "not ({node_alias})-[:precedes*]->({{id: {id_string}}})"


class NotFollowsClauseElement(PrecedenceClauseElement):
    value_alias_prefix = "follows_"
    template = "not ({{id: {id_string}}})-[:precedes*]->({node_alias})"


class PausePrecedenceClauseElement(PrecedenceClauseElement):
    def __init__(self, annotation):
        self.node = annotation

    def for_cypher(self):
        key = self.node.alias
        return self.template.format(alias=key)


class FollowsPauseClauseElement(PausePrecedenceClauseElement):
    template = "(:pause)-[:precedes_pause]->({alias})"


class NotFollowsPauseClauseElement(PausePrecedenceClauseElement):
    template = "not (:pause)-[:precedes_pause]->({alias})"


class PrecedesPauseClauseElement(PausePrecedenceClauseElement):
    template = "({alias})-[:precedes_pause]->(:pause)"


class NotPrecedesPauseClauseElement(PausePrecedenceClauseElement):
    template = "not ({alias})-[:precedes_pause]->(:pause)"


class SubsetClauseElement(AnnotationClauseElement):
    template = "{}:{}"

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        value = key_for_cypher(self.value)
        if self.attribute.node.hierarchy.has_token_subset(
            self.attribute.node.node_type, self.value
        ):
            key = self.attribute.node.alias
        else:
            key = self.attribute.node.type_alias
        return self.template.format(key, value)


class NotSubsetClauseElement(SubsetClauseElement):
    template = "NOT {}:{}"


class ContainsClauseElement(AnnotationClauseElement):
    """
    Clause for filtering based on hierarchical relations.
    """

    sign = "contains"
    template = """({alias})<-[:contained_by]-({token})-[:is_a]->({type} {{{label}: {value}}})"""

    def for_cypher(self):
        kwargs = {
            "alias": self.attribute.annotation.alias,
            "value": value_for_cypher(self.value),
            "label": key_for_cypher(self.attribute.label),
            "type": ":{}_type".format(self.attribute.node.node_type),
            "token": ":{}".format(self.attribute.node.node_type),
        }
        return self.template.format(**kwargs)


class AlignmentClauseElement(AnnotationClauseElement):
    """
    Base class for filtering based on alignment.
    """

    template = "{first}.label = {second}.label"
    side = ""
    aligned = True

    def __init__(self, first, second):
        from .attributes import HierarchicalAnnotation

        self.first = first

        if not isinstance(first, HierarchicalAnnotation) and not isinstance(
            second, HierarchicalAnnotation
        ):
            second = getattr(self.first, second.node_type)
        self.second = second

    def __hash__(self):
        return hash((self.first, self.template, self.second))

    def for_json(self):
        if self.side == "left":
            att = "begin"
        else:
            att = "end"
        if self.aligned:
            op = "=="
        else:
            op = "!="
        return [
            [[x for x in self.first.for_json()] + [att]],
            op,
            [[x for x in self.first.for_json()] + [att]],
        ]

    @property
    def nodes(self):
        """
        Returns
        -------
        first and second annotations
        """
        return self.first.nodes + self.second.nodes

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
        kwargs = {
            "second_node_alias": self.second.alias,
            "first_node_alias": self.first.alias,
        }
        return self.template.format(**kwargs)

    def is_matrix(self):
        from .attributes import SubPathAnnotation

        if isinstance(self.first, SubPathAnnotation):
            return False
        if isinstance(self.second, SubPathAnnotation):
            return False
        return True

    def involves(self, annotation):
        from ...exceptions import AnnotationAttributeError
        from .attributes import SubPathAnnotation

        to_match = "alias"
        if isinstance(annotation, SubPathAnnotation):
            to_match = "collection_alias"
        try:
            if getattr(self.first, to_match, None) == getattr(annotation, to_match):
                return True
            if getattr(self.second, to_match, None) == getattr(annotation, to_match):
                return True
        except AnnotationAttributeError:
            pass
        return False


class RightAlignedClauseElement(AlignmentClauseElement):
    """
    Clause for filtering based on right alignment.
    """

    template = """not ({first_node_alias})-[:precedes]->()-[:contained_by]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by]->({second_node_alias})"""
    side = "right"
    aligned = True


class LeftAlignedClauseElement(AlignmentClauseElement):
    """
    Clause for filtering based on left alignment.
    """

    template = """not ({first_node_alias})<-[:precedes]-()-[:contained_by]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by]->({second_node_alias})"""
    side = "left"
    aligned = True


class NotRightAlignedClauseElement(RightAlignedClauseElement):
    """
    Clause for filtering based on not being right aligned.
    """

    template = """({first_node_alias})-[:precedes]->()-[:contained_by]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by]->({second_node_alias})"""
    side = "right"
    aligned = False


class NotLeftAlignedClauseElement(LeftAlignedClauseElement):
    """
    Clause for filtering based on not being left aligned.
    """

    template = """({first_node_alias})<-[:precedes]-()-[:contained_by]->({second_node_alias})
    AND ({first_node_alias})-[:contained_by]->({second_node_alias})"""
    side = "left"
    aligned = False


class EqualClauseElement(AnnotationClauseElement, BaseEqualClauseElement):
    pass


class GtClauseElement(AnnotationClauseElement, BaseGtClauseElement):
    pass


class GteClauseElement(AnnotationClauseElement, BaseGteClauseElement):
    pass


class LtClauseElement(AnnotationClauseElement, BaseLtClauseElement):
    pass


class LteClauseElement(AnnotationClauseElement, BaseLteClauseElement):
    pass


class NotEqualClauseElement(AnnotationClauseElement, BaseNotEqualClauseElement):
    pass


class InClauseElement(AnnotationClauseElement, BaseInClauseElement):
    pass


class NotInClauseElement(AnnotationClauseElement, BaseNotInClauseElement):
    pass


class RegexClauseElement(AnnotationClauseElement, BaseRegexClauseElement):
    pass


class NullClauseElement(AnnotationClauseElement, BaseNullClauseElement):
    pass


class NotNullClauseElement(AnnotationClauseElement, BaseNotNullClauseElement):
    pass
