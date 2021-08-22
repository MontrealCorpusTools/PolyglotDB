from .path import SubPathAnnotation, PathAttribute


class SubAnnotation(SubPathAnnotation):
    non_optional = False
    subquery_match_template = '({def_collection_alias})-[:annotates]->({anchor_node_alias})'

    def __repr__(self):
        return '<SubAnnotation of {} under {}'.format(str(self.collected_node), str(self.anchor_node))

    def __getattr__(self, key):
        from .path import PositionalAnnotation
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

        return PathAttribute(self, key)

    @property
    def with_pre_collection(self):
        return ', '.join([self.collection_alias])

    @property
    def withs(self):
        withs = [self.collection_alias]
        return withs

    def with_statement(self):
        withs = [self.collect_template.format(a=self.collection_alias)
                 ]
        return ', '.join(withs)
