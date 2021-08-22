from .base import AnnotationNode, AnnotationCollectionNode, AnnotationCollectionAttribute, special_attributes, \
    key_for_cypher


class SubPathAnnotation(AnnotationCollectionNode):
    non_optional = False
    subquery_match_template = '({def_collection_type_alias})<-[:is_a]-({def_collection_alias})-[:contained_by{depth}]->({anchor_node_alias})'
    subquery_order_by_template = 'ORDER BY {collection_alias}.begin'
    subannotation_subquery_template = '''OPTIONAL MATCH ({def_subannotation_alias})-[:annotates]->({collection_alias})
        WITH {output_with_string}'''

    def subquery(self, withs, filters=None, optional=False):
        input_with = ', '.join(withs)
        new_withs = withs - {self.collection_alias}
        output_with = ', '.join(new_withs) + ', ' + self.with_statement()
        where_string = ''
        if filters is not None:
            relevant = []
            for c in filters:
                if c.involves(self):
                    relevant.append(c.for_cypher())
            if relevant:
                where_string = 'WHERE ' + '\nAND '.join(relevant)
        depth = self.hierarchy.get_depth(self.collected_node.node_type, self.anchor_node.node_type)
        depth_string = ''
        if depth > 1:
            depth_string = '*{}'.format(depth)
        for_match = self.subquery_match_template.format(anchor_node_alias=self.anchor_node.alias,
                                                        def_collection_alias=self.def_collection_alias,
                                                        def_collection_type_alias=self.def_collection_type_alias,
                                                        depth=depth_string)
        order_by = self.subquery_order_by_template.format(collection_alias=self.collection_alias)
        subannotation_query = ''
        if self.with_subannotations:
            subannotation_query = self.generate_subannotation_query(input_with)

        kwargs = {'for_match': for_match,
                  'where_string': where_string,
                  'input_with_string': input_with,
                  'order_by': order_by,
                  'optional': 'OPTIONAL ' if optional else '',
                  'sub_query': subannotation_query,
                  'with_pre_collection': self.with_pre_collection,
                  'output_with_string': output_with}
        return self.subquery_template.format(**kwargs)

    def __lt__(self, other):
        return True

    @property
    def with_pre_collection(self):
        return ', '.join([self.collection_alias, self.collection_type_alias])

    def __init__(self, anchor_node, collected_node):
        super(SubPathAnnotation, self).__init__(anchor_node, collected_node)
        self.with_subannotations = False

    def __repr__(self):
        return '<SubPathAnnotation of {} under {}'.format(str(self.collected_node), str(self.anchor_node))

    def generate_subannotation_query(self, input_with_string):
        """
        Generates a subannotation query

        Parameters
        ----------
        input_with_string : str
            the string limiting the input
        """
        output_with_string = ','.join([input_with_string, self.collection_alias,
                                       self.collection_type_alias,
                                       self.collect_template.format(a=self.subannotation_alias)])
        return self.subannotation_subquery_template.format(def_subannotation_alias=self.def_subannotation_alias,
                                                           collection_alias=self.collection_alias,
                                                           output_with_string=output_with_string)

    @property
    def subannotation_alias(self):
        return 'subannotation_' + self.collection_alias

    @property
    def def_subannotation_alias(self):
        return '{}:{}'.format(self.subannotation_alias, key_for_cypher(self.collected_node.corpus))

    @property
    def withs(self):
        withs = [self.collection_alias, self.collection_type_alias]
        if self.with_subannotations:
            withs.append(self.subannotation_alias)
        return withs

    def with_statement(self):
        withs = [self.collect_template.format(a=self.collection_alias),
                 self.collect_template.format(a=self.collection_type_alias)
                 ]
        if self.with_subannotations:
            withs.append(self.collect_template.format(a=self.subannotation_alias))
        return ', '.join(withs)

    @property
    def cache_alias(self):
        return self.anchor_node.alias

    @property
    def def_collection_type_alias(self):
        label_string = self.collected_node.node_type + '_type'
        if self.collected_node.subset_labels:
            subset_type_labels = [x for x in self.collected_node.subset_labels if
                                  self.hierarchy.has_type_subset(self.collected_node.node_type, x)]
            if subset_type_labels:
                label_string += ':' + ':'.join(map(key_for_cypher, subset_type_labels))
        return '{}:{}'.format(self.collection_type_alias, label_string)

    @property
    def def_collection_alias(self):
        label_string = ':{}'.format(self.collected_node.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.collected_node.corpus))
        if self.collected_node.subset_labels:
            subset_token_labels = [x for x in self.collected_node.subset_labels if
                                  self.hierarchy.has_token_subset(self.collected_node.node_type, x)]
            if subset_token_labels:
                label_string += ':' + ':'.join(map(key_for_cypher, subset_token_labels))
        return '{}{}'.format(self.collection_alias, label_string)

    @property
    def collection_type_alias(self):
        a = 'type_' + self.collection_alias
        a = a.replace('`', '')
        return key_for_cypher(a)

    @property
    def key(self):
        return self.collected_node.key

    @property
    def alias(self):
        return self.collected_node.alias

    def __getattr__(self, key):
        if key == 'annotation':
            raise (AttributeError('Annotations cannot have annotations.'))
        if key == 'initial':
            return PositionalAnnotation(self, 0)
        elif key == 'final':
            return PositionalAnnotation(self, -1)
        elif key == 'penultimate':
            return PositionalAnnotation(self, -2)
        elif key == 'antepenultimate':
            return PositionalAnnotation(self, -3)
        elif self.hierarchy is not None \
                and self.collected_node.node_type in self.hierarchy.subannotations \
                and key in self.hierarchy.subannotations[self.collected_node.node_type]:
            from .subannotation import SubAnnotation
            return SubAnnotation(self, AnnotationNode(key, corpus=self.collected_node.corpus))

        if key not in special_attributes and self.hierarchy is not None and not self.hierarchy.has_token_property(
                self.collected_node.node_type, key) and not self.hierarchy.has_type_property(self.collected_node.node_type, key):
            raise (
                AttributeError(
                    'The \'{}\' annotation types do not have a \'{}\' property.'.format(self.collected_node.node_type, key)))
        return PathAttribute(self, key)


class PositionalAnnotation(SubPathAnnotation):
    def __init__(self, path_annotation, pos):
        self.node = path_annotation
        self.pos = pos
        self.subset_labels = []

    def __repr__(self):
        return '<PositionalAnnotation object with \'{}\' type and {} position>'.format(self.node.node_type, self.pos)

    def __getattr__(self, key):
        return PositionalAttribute(self, key)

    @property
    def node_type(self):
        return self.node.node_type

    @property
    def anchor_node(self):
        return self.node.anchor_node

    @property
    def collected_node(self):
        return self.node.collected_node

    @property
    def collection_alias(self):
        return self.node.collection_alias

    @property
    def withs(self):
        return [self.collection_alias, self.collection_type_alias]

    @property
    def collection_type_alias(self):
        return self.node.collection_type_alias


class PathAttribute(AnnotationCollectionAttribute):
    collapsing = True
    filter_template = '{alias}.{property}'
    return_template = '[n in {alias}|n.{property}]'
    duration_return_template = '[n in {alias}|n.end - n.begin]'
    count_return_template = 'size({alias})'
    rate_return_template = 'case when ({node_alias}.end - {node_alias}.begin) = 0 then null else size({alias}) / ({node_alias}.end - {node_alias}.begin) end'
    position_return_template = 'reduce(count = 1, n in [x in {alias} where x.begin < {node_alias}.begin | x] | count + 1)'

    def __repr__(self):
        return '<PathAttribute \'{}\'>'.format(str(self))

    def for_return(self):
        if self.label == 'duration':
            return self.duration_return_template.format(alias=self.node.collection_alias)
        elif self.label == 'count':
            return self.count_return_template.format(alias=self.node.collection_alias)
        elif self.label == 'rate':
            return self.rate_return_template.format(alias=self.node.collection_alias,
                                                    node_alias=self.node.anchor_node.alias)
        elif self.label == 'position':
            return self.position_return_template.format(alias=self.node.collection_alias,
                                                        node_alias=self.node.collected_node.alias)
        if self.requires_type():
            return self.return_template.format(alias=self.node.collection_type_alias, property=self.label)
        return self.return_template.format(alias=self.node.collection_alias, property=self.label)

    def for_filter(self):
        return self.filter_template.format(alias=self.node.collection_alias, property=self.label)

    def requires_type(self):
        from .subannotation import SubAnnotation
        if isinstance(self.node, SubAnnotation):
            return False
        if self.node.hierarchy.has_token_property(self.node.node_type, self.label):
            return False
        return True

    @property
    def with_aliases(self):
        """Returns annotation withs list """
        return self.node.withs

    @property
    def with_alias(self):
        return self.node.collection_alias


class PositionalAttribute(PathAttribute):
    return_template = '[n in {alias}|n.{property}][{pos}]'

    def __repr__(self):
        return '<PositionalAttribute \'{}\'>'.format(str(self))

    @property
    def with_alias(self):
        if self.requires_type():
            return self.node.node.collection_type_alias
        return self.node.node.collection_alias

    def for_return(self, type=False):
        """
        Generates a cypher string for type return

        Returns
        -------
        type_return_template : str
            A string with positional properties
        """
        pos = self.node.pos
        if self.label == 'duration':
            alias = self.node.collection_alias
            beg = self.return_template.format(alias=alias, property='begin', pos=pos)
            end = self.return_template.format(alias=alias, property='end', pos=pos)
            return '{} - {}'.format(end, beg)
        if type or self.requires_type():
            alias = self.node.collection_type_alias
        else:
            alias = self.node.collection_alias
        return self.return_template.format(alias=alias, property=self.label, pos=pos)
