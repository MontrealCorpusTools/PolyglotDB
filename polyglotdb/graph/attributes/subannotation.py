
from ..helper import key_for_cypher

from .path import SubPathAnnotation, PathAttribute

class SubAnnotation(SubPathAnnotation):
    subquery_template = '''OPTIONAL MATCH ({def_path_alias})-[:annotates]->({alias})
        {where_string}
        WITH {input_with_string}, {path_alias}
        ORDER BY {path_alias}.begin
        WITH {output_with_string}'''

    def generate_subquery(self, output_with_string, input_with_string, filters = None):
        """
        Generates a subquery 
        
        Parameters
        ----------
        output_with_string : str
            the string limiting the output
        input_with_string : str
            the string limiting the input
         """
        where_string = ''
        if filters is not None:
            relevant = []
            for c in filters:
                if c.involves(self):
                    relevant.append(c.for_cypher())
            if relevant:
                where_string = 'WHERE '+ '\nAND '.join(relevant)
        return self.subquery_template.format(alias = self.annotation.alias,
                        input_with_string = input_with_string, output_with_string = output_with_string,
                        def_path_alias = self.def_path_alias, path_alias = self.path_alias, where_string = where_string)

    @property
    def withs(self):
        """ Returns 1-element list containing path_alias"""
        return [self.path_alias]

    def with_statement(self):
        """Returns cypher formatted collect statement """
        template = 'collect({a}) as {a}'
        return template.format(a=self.path_alias)

    @property
    def path_alias(self):
        """Returns cypher formatted string containing subannotation alias and annotation alias"""
        return key_for_cypher('{}_of_{}'.format(self.sub.alias, self.annotation.alias))

    @property
    def def_path_alias(self):
        """Returns cypher formatted string containing path_alias, subannotation type, and corpus"""
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
