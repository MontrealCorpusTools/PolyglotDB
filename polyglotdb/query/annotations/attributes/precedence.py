from .base import AnnotationNode
from ...base.helper import key_for_cypher
from ....exceptions import AnnotationAttributeError


class PrecedenceAnnotation(AnnotationNode):
    non_optional = False
    match_template = '({anchor_alias})-[:precedes]-({token_alias})-[:is_a]->({type_alias})'
    alias_prefix = ''

    def __init__(self, node, pos):
        super(PrecedenceAnnotation, self).__init__(node.node_type, node.corpus, node.hierarchy)
        self.anchor_node = node
        try:
            pos += node.pos
        except AnnotationAttributeError:
            pass
        self.pos = pos

    def __hash__(self):
        return hash(self.key)

    @property
    def key(self):
        return self.alias_prefix + '{}_'.format(abs(self.pos)) + self.anchor_node.key

    def __eq__(self, other):
        if not isinstance(other, PrecedenceAnnotation):
            return False
        if self.anchor_node != other.anchor_node:
            return False
        if self.pos != other.pos:
            return False
        return True

    @property
    def alias(self):
        """Returns a cypher formatted string of keys and prefixes"""
        return key_for_cypher(self.alias_template.format(t=self.key, prefix=''))

    def for_match(self):
        """ sets 'token_alias' and 'type_alias'  keyword arguments for an annotation """
        kwargs = {'token_alias': self.define_alias,
                  'type_alias': self.define_type_alias,
                  'anchor_alias': self.anchor_node.alias}
        return self.match_template.format(**kwargs)

    @property
    def nodes(self):
        return [self] + self.anchor_node.nodes


class FollowingAnnotation(PrecedenceAnnotation):
    alias_prefix = 'foll_'
    match_template = '({anchor_alias})-[:precedes]->({token_alias})-[:is_a]->({type_alias})'

    def __repr__(self):
        return '<FollowingAnnotation of {} with position {}>'.format(self.node_type, self.pos)

    def for_json(self):
        out = self.anchor_node.for_json()
        out.append('following')
        return out

    def __lt__(self, other):
        if isinstance(other, PreviousAnnotation):
            return False
        if not isinstance(other, FollowingAnnotation):
            return True
        if self.pos < other.pos:
            return True
        return False


class PreviousAnnotation(PrecedenceAnnotation):
    alias_prefix = 'prev_'
    match_template = '({anchor_alias})<-[:precedes]-({token_alias})-[:is_a]->({type_alias})'

    def __repr__(self):
        return '<PreviousAnnotation of {} with position {}>'.format(self.node_type, self.pos)

    def for_json(self):
        out = self.anchor_node.for_json()
        out.append('previous')
        return out

    def __lt__(self, other):
        if isinstance(other, FollowingAnnotation):
            return True
        if not isinstance(other, PreviousAnnotation):
            return True
        if self.pos > other.pos:
            return True
        return False
