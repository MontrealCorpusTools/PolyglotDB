
from ..helper import key_for_cypher

from .base import AnnotationAttribute

class HierarchicalAnnotation(AnnotationAttribute):
    template = '''({contained_alias})-[:contained_by{depth}]->({containing_alias})-[:is_a]->({containing_type_alias})'''
    #template = '''({contained_alias})-[:contained_by*{depth}]->({containing_alias})'''

    def __init__(self, type, contained_annotation, corpus = None, hierarchy = None):
        self.type = type
        self.contained_annotation = contained_annotation

        self.corpus = corpus
        self.subset_type_labels = []
        self.subset_token_labels = []
        self.hierarchy = hierarchy

        if self.hierarchy is None:
            self.depth = '1..'
        else:
            self.depth = 1
            t = self.hierarchy.get_higher_types(contained_annotation.type)
            for i in t:
                if i == self.type:
                    break
                self.depth += 1

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
        if self.depth != 1:
            kwargs['depth'] = '*' + str(self.depth)
        else:
            kwargs['depth'] = ''
        return self.template.format(**kwargs)

