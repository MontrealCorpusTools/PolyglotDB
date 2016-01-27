
from ..helper import key_for_cypher

from .base import AnnotationAttribute

class HierarchicalAnnotation(AnnotationAttribute):
    template = '''({contained_alias})-[:contained_by*1..]->({containing_alias})-[:is_a]->({containing_type_alias})'''

    def __init__(self, type, contained_annotation, corpus = None, hierarchy = None):
        self.type = type
        self.contained_annotation = contained_annotation

        self.corpus = corpus
        self.subset_type_labels = []
        self.subset_token_labels = []
        self.hierarchy = hierarchy

    def __repr__(self):
        return '<HierarchicalAnnotation object of \'{}\' type from \'{}\'>'.format(self.type, self.contained_annotation.type)

    @property
    def pos(self):
        return 0

    @property
    def alias(self):
        return key_for_cypher(self.contained_annotation.alias.replace('`','') + '_' + self.type)

    def for_match(self):
        kwargs = {}
        kwargs['contained_alias'] = self.contained_annotation.alias
        kwargs['containing_alias'] = self.define_alias
        kwargs['containing_type_alias'] = self.define_type_alias
        return self.template.format(**kwargs)

