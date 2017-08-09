from .base import Node, NodeAttribute, key_for_cypher
from ....exceptions import AnnotationAttributeError



class SpeakerAnnotation(Node):
    match_template = '''({token_alias})-[:spoken_by]->({alias})'''

    def __repr__(self):
        return '<SpeakerAnnotation \'{}\'>'.format(str(self))

    def __init__(self, annotation_node):
        super(SpeakerAnnotation, self).__init__('Speaker', annotation_node.corpus, annotation_node.hierarchy)
        self.annotation_node = annotation_node

    @property
    def define_alias(self):
        label_string = ':{}'.format(self.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        return '{}{}'.format(self.alias, label_string)

    def for_match(self):
        kwargs = {'token_alias': self.annotation_node.alias,
                  'alias': self.define_alias}
        return self.match_template.format(**kwargs)

    @property
    def withs(self):
        return [self.alias]

    def __getattr__(self, key):
        if self.hierarchy is not None and not self.hierarchy.has_speaker_property(key):
            props = [x[0] for x in self.hierarchy.speaker_properties]
            raise AnnotationAttributeError('Speakers do not have a "{}" property, available are: .'.format(key, ', '.join(props)))
        return NodeAttribute(self, key)
