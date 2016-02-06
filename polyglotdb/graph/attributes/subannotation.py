
from ..helper import key_for_cypher

from .path import SubPathAnnotation

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

