
from ..helper import key_for_cypher

from .path import SubPathAnnotation, PathAttribute

class SubAnnotation(SubPathAnnotation):
    subquery_template = '''OPTIONAL MATCH ({def_path_alias})-[:annotates]->({alias})
        WITH {input_with_string}, {path_alias}
        ORDER BY {path_alias}.begin
        WITH {output_with_string}'''

    def generate_subquery(self, output_with_string, input_with_string):
        return self.subquery_template.format(alias = self.annotation.alias,
                        input_with_string = input_with_string, output_with_string = output_with_string,
                        def_path_alias = self.def_path_alias, path_alias = self.path_alias)

    @property
    def withs(self):
        return [self.path_alias]

    def with_statement(self):
        template = 'collect({a}) as {a}'
        return template.format(a=self.path_alias)

    @property
    def path_alias(self):
        return key_for_cypher('{}_of_{}'.format(self.sub.alias, self.annotation.alias))

    @property
    def def_path_alias(self):
        return '{}:{}:{}'.format(self.path_alias, self.sub.type, self.sub.corpus)

    def __getattr__(self, key):
        if key == 'annotation':
            raise(AttributeError('Annotations cannot have annotations.'))
        if key == 'initial':
            return PositionalAnnotation(self, 0)
        elif key == 'final':
            return PositionalAnnotation(self, -1)
        elif key == 'penultimate':
            return PositionalAnnotation(self, -2)
        elif key == 'antepenultimate':
            return PositionalAnnotation(self, -3)
        elif self.hierarchy is not None \
                and self.type in self.hierarchy.subannotations \
                and key in self.hierarchy.subannotations[self.type]:
            from .subannotation import SubAnnotation
            return SubAnnotation(self, AnnotationAttribute(key, self.annotation.pos, corpus = self.annotation.corpus))

        type = False
        return PathAttribute(self, key, type)
