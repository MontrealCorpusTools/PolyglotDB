from .base import AnnotationNode, key_for_cypher


class HierarchicalAnnotation(AnnotationNode):
    match_template = '''({anchor_alias})-[:contained_by]->({higher_alias})-[:is_a]->({higher_type_alias})'''

    # template = '''({contained_alias})-[:contained_by*{depth}]->({containing_alias})'''

    def __init__(self, anchor_node, higher_node):
        super(HierarchicalAnnotation, self).__init__(higher_node.node_type, higher_node.corpus, higher_node.hierarchy)
        self.anchor_node = anchor_node
        self.higher_node = higher_node

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, HierarchicalAnnotation):
            return False
        if self.anchor_node != other.anchor_node:
            return False
        if self.higher_node != other.higher_node:
            return False
        return True

    @property
    def key(self):
        return self.anchor_node.key + "_" + self.higher_node.node_type

    @property
    def nodes(self):
        return [self] + self.anchor_node.nodes

    def for_json(self):
        base = [x for x in self.anchor_node.for_json()] + [self.node_type]
        return base

    def hierarchy_path(self, to_find):
        """ 
        Generates a path for the hierarchy

        Returns
        -------
        real_path : list

        """
        path = [self.node_type]
        a = self.contained_annotation
        while True:
            path.insert(0, a.node_type)
            if not isinstance(a, HierarchicalAnnotation):
                break
            a = a.contained_annotation
        real_path = [path[0]]
        while real_path[-1] != self.node_type:
            real_path.append(self.hierarchy[real_path[-1]])
        return real_path

    def __repr__(self):
        return '<HierarchicalAnnotation object of \'{}\' type from \'{}\'>'.format(self.node_type,
                                                                                   self.anchor_node.node_type)

    # def __getattr__(self, key):
    #     if key == 'annotation':
    #         raise (AttributeError('Annotations do not have annotation attributes.'))
    #     if key in ['previous', 'following']:
    #         from .precedence import PreviousAnnotation, FollowingAnnotation
    #         if key == 'previous':
    #             return PreviousAnnotation(self, -1)
    #         else:
    #             return FollowingAnnotation(self, -1)
    #     elif key == 'speaker':
    #         from .speaker import SpeakerAnnotation
    #         return SpeakerAnnotation(self)
    #     elif key == 'discourse':
    #         from .discourse import DiscourseAnnotation
    #         return DiscourseAnnotation(self)
    #     elif key == 'pause':
    #         from .pause import PauseAnnotation
    #         return PauseAnnotation(self.pos, corpus=self.corpus, hierarchy=self.hierarchy)
    #     elif key.startswith('pitch'):
    #         from .acoustic import PitchAttribute
    #         return PitchAttribute(self, relative=('relative' in key))
    #     elif key.startswith('intensity'):
    #         from .acoustic import IntensityAttribute
    #         return IntensityAttribute(self, relative=('relative' in key))
    #     elif key.startswith('formants'):
    #         from .acoustic import FormantAttribute
    #         return FormantAttribute(self, relative=('relative' in key))
    #     elif self.hierarchy is not None and key in self.hierarchy.contained_by(self.node_type):
    #         types = self.hierarchy.get_higher_types(self.node_type)
    #         prev_node = self
    #         cur_node = None
    #         for t in types:
    #             higher_node = AnnotationNode(t, corpus=self.corpus, hierarchy=self.hierarchy)
    #             cur_node = HierarchicalAnnotation(prev_node, higher_node)
    #             prev_node = cur_node
    #             if t == key:
    #                 break
    #         return cur_node
    #     elif self.hierarchy is not None and key in self.hierarchy.contains(self.node_type):
    #         from .path import SubPathAnnotation
    #         return SubPathAnnotation(self, AnnotationNode(key, self.pos, corpus=self.corpus))
    #     elif self.hierarchy is not None \
    #             and self.node_type in self.hierarchy.subannotations \
    #             and key in self.hierarchy.subannotations[self.node_type]:
    #         from .subannotation import SubAnnotation
    #         return SubAnnotation(self, AnnotationNode(key, self.pos, corpus=self.corpus))
    #     else:
    #         if key not in special_attributes and self.hierarchy is not None and not self.hierarchy.has_type_property(
    #                 self.node_type, key) and not self.hierarchy.has_token_property(self.node_type, key):
    #             raise (
    #                 AnnotationAttributeError(
    #                     'The \'{}\' annotation types do not have a \'{}\' property.'.format(self.node_type, key)))
    #         return AnnotationAttribute(self, key)

    @property
    def alias(self):

        """Returns a cypher formatted string of keys and prefixes"""

        pre = ''
        #if self.pos < 0:
        #    pre += 'prev_{}_'.format(-1 * self.pos)
        #elif self.pos > 0:
        #    pre += 'foll_{}_'.format(self.pos)
        return key_for_cypher(pre + self.anchor_node.alias.replace('`', '') + '_' + self.node_type)

    def for_match(self):
        kwargs = {'anchor_alias': self.anchor_node.alias,
                  'higher_alias': self.define_alias,
                  'higher_type_alias': self.define_type_alias}
        return self.match_template.format(**kwargs)
