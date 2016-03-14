
from polyglotdb.graph.attributes.base import AnnotationAttribute, Attribute

from polyglotdb.graph.attributes.path import PathAnnotation, PathAttribute

class PauseAnnotation(AnnotationAttribute):
    def __init__(self, pos = 0, corpus = None, hierarchy = None):
        self.type = 'pause'
        self.pos = pos
        self.corpus = corpus
        self.hierarchy = hierarchy
        self.subset_token_labels = []
        self.subset_type_labels = []

    @property
    def define_alias(self):
        label_string = ':{}'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        return '{}{}'.format(self.alias, label_string)

    def __getattr__(self, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return PausePathAnnotation(self.type, pos, corpus = self.corpus, hierarchy = self.hierarchy)

        return PauseAttribute(self, key, False)

    @property
    def key(self):
        return 'pause'

class PauseAttribute(Attribute):
    pass

class PausePathAnnotation(PathAnnotation):
    def additional_where(self):
        if self.key == 'pause':
            return 'NONE (x in nodes({})[1..-1] where x:speech)'.format(self.path_alias)
        return None

    def __getattr__(self, key):
        if key == 'annotation':
            raise(AttributeError('Annotations cannot have annotations.'))
        return PausePathAttribute(self, key, False)

class PausePathAttribute(PathAttribute):
    duration_return_template = 'extract(n in nodes({alias})[-1..]| n.end)[0] - extract(n in nodes({alias})[0..1]| n.begin)[0]'

    @property
    def with_alias(self):
        return self.annotation.path_type_alias
