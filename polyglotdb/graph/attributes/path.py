
from ..helper import key_for_cypher, type_attributes

from .base import AnnotationAttribute, Attribute

class PathAnnotation(AnnotationAttribute):
    has_subquery = True
    path_prefix = 'path_'

    subquery_template = '''UNWIND (CASE WHEN length({path_alias}) > 0 THEN nodes({path_alias})[1..-1] ELSE [null] END) as n
        OPTIONAL MATCH (n)-[:is_a]->({path_type_alias})
        WITH {output_with_string}'''

    def subquery(self, withs):
        input_with = ', '.join(withs)
        new_withs = withs - set([self.path_alias])
        output_with = ', '.join(new_withs) + ', ' + self.with_statement()
        return self.generate_subquery(output_with, input_with)


    def generate_times_subquery(self, output_with_string, input_with_string):
        return '''WITH {}'''.format(output_with_string)

    def generate_subquery(self, output_with_string, input_with_string):
        return self.subquery_template.format(path_alias = self.path_alias,
                        output_with_string = output_with_string,
                        key = self.key,
                        path_type_alias = self.def_path_type_alias)



    def with_statement(self):
        return ', '.join(['collect(n) as {a}'.format(a=self.path_alias),
                    'collect(t) as {a}'.format(a=self.path_type_alias)])
    @property
    def def_path_type_alias(self):
        label_string = self.type + '_type'
        if self.subset_type_labels:
            label_string += ':' + ':'.join(map(key_for_cypher, self.subset_type_labels))
        return 't:{}'.format(label_string)

    @property
    def def_path_alias(self):
        return '{}:{}:{}'.format(self.path_alias, self.key, self.sub.corpus)

    @property
    def path_alias(self):
        pre = ''
        if self.pos < 0:
            pre += 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre += 'foll_{}_'.format(self.pos)
        return key_for_cypher('{}{}'.format(pre, self.key))

    alias = path_alias

    @property
    def path_type_alias(self):
        a = 'type_'+self.path_alias
        a = a.replace('`','')
        return key_for_cypher(a)

    @property
    def key(self):
        return 'pause'

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
            return SubAnnotation(self, AnnotationAttribute(key, self.pos, corpus = self.corpus))
        return PathAttribute(self, key)

class SubPathAnnotation(PathAnnotation):
    subquery_template = '''MATCH ({def_path_type_alias})<-[:is_a]-({def_path_alias})-[:contained_by*]->({alias})
        WITH {input_with_string}, {path_type_alias}, {path_alias}
        {subannotation_query}
        ORDER BY {path_alias}.begin
        WITH {output_with_string}'''

    subannotation_subquery_template = '''OPTIONAL MATCH ({def_subannotation_alias})-[:annotates]->({path_alias})
        WITH {output_with_string}'''

    collect_template = 'collect({a}) as {a}'
    def __init__(self, super_annotation, sub_annotation):
        self.annotation = super_annotation
        self.sub = sub_annotation
        self.with_subannotations = False

    @property
    def hierarchy(self):
        return self.annotation.hierarchy

    @property
    def type(self):
        return self.sub.type

    def __hash__(self):
        return hash((self.annotation, self.sub))

    def generate_subquery(self, output_with_string, input_with_string):
        if self.with_subannotations:
            subannotation_query = self.generate_subannotation_query(input_with_string)
        else:
            subannotation_query = ''
        return self.subquery_template.format(alias = self.annotation.alias,
                        input_with_string = input_with_string, output_with_string = output_with_string,
                        path_type_alias = self.path_type_alias, def_path_type_alias = self.def_path_type_alias,
                        def_path_alias = self.def_path_alias, path_alias = self.path_alias,
                        subannotation_query = subannotation_query)

    def generate_subannotation_query(self, input_with_string):
        output_with_string = ','.join([input_with_string, self.path_alias,
                                self.path_type_alias,
                                self.collect_template.format(a = self.subannotation_alias)])
        return self.subannotation_subquery_template.format(def_subannotation_alias = self.def_subannotation_alias,
                            path_alias = self.path_alias, output_with_string = output_with_string)

    @property
    def subannotation_alias(self):
        return 'subannotation_'+ self.path_alias

    @property
    def def_subannotation_alias(self):
        return '{}:{}'.format(self.subannotation_alias, self.sub.corpus)

    @property
    def withs(self):
        withs = [self.path_alias,self.path_type_alias]
        if self.with_subannotations:
            withs.append(self.subannotation_alias)
        return withs

    def with_statement(self):
        withs = [self.collect_template.format(a=self.path_alias),
                    self.collect_template.format(a=self.path_type_alias)
                    ]
        if self.with_subannotations:
            withs.append(self.collect_template.format(a=self.subannotation_alias))
        return ', '.join(withs)

    @property
    def def_path_type_alias(self):
        label_string = self.sub.type + '_type'
        if self.sub.subset_type_labels:
            label_string += ':' + ':'.join(map(key_for_cypher, self.sub.subset_type_labels))
        return '{}:{}'.format(self.path_type_alias,label_string)

    @property
    def def_path_alias(self):
        return '{}:{}:{}'.format(self.path_alias, self.sub.type, self.sub.corpus)

    @property
    def path_alias(self):
        return key_for_cypher('{}_in_{}'.format(self.sub.alias, self.annotation.alias))

    def subset_type(self, *args):
        self.sub = self.sub.subset_type(*args)
        return self

    def subset_token(self, *args):
        self.sub.subset_token_labels.extend(args)
        return self

    @property
    def path_type_alias(self):
        a = 'type_'+self.path_alias
        a = a.replace('`','')
        return key_for_cypher(a)

    @property
    def key(self):
        return self.sub.key

    @property
    def alias(self):
        return self.sub.alias

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
        return PathAttribute(self, key)

class PositionalAnnotation(SubPathAnnotation):
    def __init__(self, path_annotation, pos):
        self.annotation = path_annotation
        self.pos = pos
        self.subset_token_labels = []
        self.subset_type_labels = []

    def __getattr__(self, key):
        if key == 'annotation':
            raise(AttributeError('Annotations cannot have annotations.'))
        return PositionalAttribute(self, key)

    def generate_subquery(self, output_with_string, input_with_string):
        return self.subquery_template.format(alias = self.annotation.annotation.alias,
                        input_with_string = input_with_string, output_with_string = output_with_string,
                        path_type_alias = self.path_type_alias, def_path_type_alias = self.def_path_type_alias,
                        def_path_alias = self.def_path_alias, path_alias = self.path_alias,
                        subannotation_query = '')

    def with_statement(self):
        return ', '.join([self.collect_template.format(a=self.path_alias),
                    self.collect_template.format(a=self.path_type_alias)])

    @property
    def type(self):
        return self.annotation.type

    @property
    def sub(self):
        return self.annotation.sub

    @property
    def path_alias(self):
        return self.annotation.path_alias

    @property
    def type_alias(self):
        return self.annotation.type_alias

    @property
    def withs(self):
        return [self.path_alias, self.path_type_alias]

    @property
    def path_type_alias(self):
        return self.annotation.path_type_alias

class PathAttribute(Attribute):
    type_return_template = 'extract(n in {alias}|n.{property})'
    duration_return_template = 'extract(n in {alias}|n.end - n.begin)'
    count_return_template = 'size({alias})'
    rate_return_template = 'size({alias}) / ({node_alias}.end - {node_alias}.begin)'
    position_return_template = 'reduce(count = 1, n in filter(x in {alias} where x.begin < {node_alias}.begin) | count + 1)'

    @property
    def base_annotation(self):
        if isinstance(self.annotation, SubPathAnnotation):
            return self.annotation.annotation
        else:
            return self.annotation

    def for_cypher(self):
        if self.label in type_attributes:
            return self.type_return_template.format(alias = self.annotation.path_type_alias, property = self.label)

        if self.label == 'duration':
            return self.duration_return_template.format(alias = self.annotation.path_alias)
        elif self.label == 'count':
            return self.count_return_template.format(alias = self.annotation.path_alias)
        elif self.label == 'rate':
            return self.rate_return_template.format(alias = self.annotation.path_type_alias, node_alias = self.base_annotation.alias)
        elif self.label == 'position':
            return self.position_return_template.format(alias = self.annotation.path_alias,
                                                    node_alias = self.annotation.sub.alias)
        else:
            return self.type_return_template.format(alias = self.annotation.path_alias, property = self.label)
    @property
    def is_type_attribute(self):
        return True

    @property
    def with_aliases(self):
        return self.annotation.withs

    @property
    def with_alias(self):
        return self.annotation.path_alias

class PositionalAttribute(PathAttribute):
    type_return_template = 'extract(n in {alias}|n.{property})[{pos}]'

    @property
    def base_annotation(self):
        return self.annotation.annotation.annotation

    @property
    def with_alias(self):
        if self.label in type_attributes + ['rate', 'count']:
            return self.annotation.annotation.path_type_alias
        return self.annotation.annotation.path_alias

    def for_cypher(self):
        pos = self.annotation.pos
        if self.label in type_attributes:
            alias = self.annotation.path_type_alias
        else:
            alias = self.annotation.path_alias
        if self.label == 'duration':
            beg = self.type_return_template.format(alias = alias, property = 'begin', pos = pos)
            end = self.type_return_template.format(alias = alias, property = 'end', pos = pos)
            return '{} - {}'.format(end, beg)
        return self.type_return_template.format(alias = alias, property = self.label, pos = pos)
