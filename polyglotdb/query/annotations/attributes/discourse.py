from .speaker import SpeakerAnnotation, AnnotationAttributeError, NodeAttribute


class DiscourseAnnotation(SpeakerAnnotation):
    match_template = '''({token_alias})-[:spoken_in]->({alias})'''

    def __repr__(self):
        return '<DiscourseAnnotation \'{}\'>'.format(str(self))

    def __init__(self, annotation_node):
        super(SpeakerAnnotation, self).__init__('Discourse', annotation_node.corpus, annotation_node.hierarchy)
        self.annotation_node = annotation_node

    def __getattr__(self, key):
        if self.hierarchy is not None and not self.hierarchy.has_discourse_property(key):
            props = [x[0] for x in self.hierarchy.discourse_properties]
            raise AnnotationAttributeError(
                'Discourses do not have a "{}" property, available are: {}.'.format(key, ', '.join(props)))
        return NodeAttribute(self, key)
