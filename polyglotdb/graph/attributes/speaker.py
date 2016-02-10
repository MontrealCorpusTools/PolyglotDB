
from ..helper import key_for_cypher

from .hierarchical import HierarchicalAnnotation

class SpeakerAnnotation(HierarchicalAnnotation):
    template = '''({token_alias})-[:spoken_by]->({speaker_alias})'''

    def __init__(self, contained_annotation, corpus = None):
        self.corpus = None
        self.type = 'Speaker'
        self.contained_annotation = contained_annotation

        self.subset_type_labels = []
        self.subset_token_labels = []

        self.hierarchy = None

    @property
    def pos(self):
        return 0

    @property
    def define_alias(self):
        label_string = ':{}'.format(self.type)
        if self.corpus is not None:
            label_string += ':{}'.format(self.corpus)
        return '{}{}'.format(self.alias, label_string)


    def for_match(self):
        kwargs = {}
        kwargs['token_alias'] = self.contained_annotation.alias
        kwargs['speaker_alias'] = self.define_alias
        return self.template.format(**kwargs)

    @property
    def withs(self):
        return [self.alias]
