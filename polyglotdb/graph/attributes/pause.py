
from .base import AnnotationAttribute, Attribute

from .path import PathAnnotation

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
            return PathAnnotation(self.type, pos, corpus = self.corpus, hierarchy = self.hierarchy)

        return Attribute(self, key)

    @property
    def key(self):
        return 'pause'

