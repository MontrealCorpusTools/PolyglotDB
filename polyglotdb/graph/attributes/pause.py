
from .base import AnnotationAttribute, Attribute

class PauseAnnotation(AnnotationAttribute):
    def __init__(self, pos = 0, corpus = None, contains = None):
        self.type = 'pause'
        self.pos = pos
        self.corpus = corpus
        self.contains = contains
        self.discourse_label = None
        self.subset_token_labels = []
        self.subset_type_labels = []

    @property
    def define_alias(self):
        label_string = ':{}:pause'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        if self.discourse_label is not None:
            label_string += ':{}'.format(self.discourse_label)
        return '{}{}'.format(self.alias, label_string)

    def __getattr__(self, key):
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return PathAnnotation(self.type, pos, corpus = self.corpus, contains = self.contains)

        return Attribute(self, key)

    @property
    def key(self):
        return 'pause'

