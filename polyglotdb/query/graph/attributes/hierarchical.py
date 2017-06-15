from ..helper import key_for_cypher

from .base import AnnotationAttribute, Attribute, special_attributes


class HierarchicalAnnotation(AnnotationAttribute):
    template = '''({contained_alias})-[:contained_by{depth}]->({containing_alias})-[:is_a]->({containing_type_alias})'''

    # template = '''({contained_alias})-[:contained_by*{depth}]->({containing_alias})'''

    def __init__(self, type, contained_annotation, pos=0, corpus=None, hierarchy=None):
        self.type = type
        self.contained_annotation = contained_annotation
        self.pos = pos

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

    def for_json(self):
        base = [x for x in self.contained_annotation.for_json()] + [self.type]
        if self.pos > 0:
            for i in range(self.pos):
                base.append('following')
        elif self.pos < 0:
            for i in range(self.pos, 0):
                base.append('previous')
        return base

    def hierarchy_path(self, to_find):
        """ 
        Generates a path for the hierarchy

        Returns
        -------
        real_path : list

        """
        path = [self.type]
        a = self.contained_annotation
        while True:
            path.insert(0, a.type)
            if not isinstance(a, HierarchicalAnnotation):
                break
            a = a.contained_annotation
        real_path = [path[0]]
        while real_path[-1] != self.type:
            real_path.append(self.hierarchy[real_path[-1]])
        return real_path

    def __repr__(self):
        return '<HierarchicalAnnotation object of \'{}\' type from \'{}\'>'.format(self.type,
                                                                                   self.contained_annotation.type)

    def __getattr__(self, key):
        if key == 'annotation':
            raise (AttributeError('Annotations do not have annotation attributes.'))
        if key in ['previous', 'following']:
            if key == 'previous':
                pos = self.pos - 1
            else:
                pos = self.pos + 1
            return HierarchicalAnnotation(self.type, self.contained_annotation, pos=pos, corpus=self.corpus,
                                          hierarchy=self.hierarchy)
        elif key == 'speaker':
            from .speaker import SpeakerAnnotation
            return SpeakerAnnotation(self, corpus=self.corpus)
        elif key == 'discourse':
            from .discourse import DiscourseAnnotation
            return DiscourseAnnotation(self, corpus=self.corpus)
        elif key == 'pause':
            from .pause import PauseAnnotation
            return PauseAnnotation(self.pos, corpus=self.corpus, hierarchy=self.hierarchy)
        elif key.startswith('pitch'):
            from .acoustic import PitchAttribute
            return PitchAttribute(self, relative=('relative' in key))
        elif key.startswith('intensity'):
            from .acoustic import IntensityAttribute
            return IntensityAttribute(self, relative=('relative' in key))
        elif key.startswith('formants'):
            from .acoustic import FormantAttribute
            return FormantAttribute(self, relative=('relative' in key))
        elif self.hierarchy is not None and key in self.hierarchy.contained_by(self.type):
            return HierarchicalAnnotation(key, self, corpus=self.corpus, hierarchy=self.hierarchy)
        elif self.hierarchy is not None and key in self.hierarchy.contains(self.type):
            from .path import SubPathAnnotation
            return SubPathAnnotation(self, AnnotationAttribute(key, self.pos, corpus=self.corpus))
        elif self.hierarchy is not None \
                and self.type in self.hierarchy.subannotations \
                and key in self.hierarchy.subannotations[self.type]:
            from .subannotation import SubAnnotation
            return SubAnnotation(self, AnnotationAttribute(key, self.pos, corpus=self.corpus))
        else:
            if self.hierarchy is None or key in special_attributes:
                type = False
            else:
                if self.hierarchy.has_type_property(self.type, key):
                    type = True
                elif self.hierarchy.has_token_property(self.type, key):
                    type = False
                else:
                    raise (
                    AttributeError('The \'{}\' annotation types do not have a \'{}\' property.'.format(self.type, key)))
            return Attribute(self, key, type)

    @property
    def alias(self):

        """Returns a cypher formatted string of keys and prefixes"""

        pre = ''
        if self.pos < 0:
            pre += 'prev_{}_'.format(-1 * self.pos)
        elif self.pos > 0:
            pre += 'foll_{}_'.format(self.pos)
        return key_for_cypher(pre + self.contained_annotation.alias.replace('`', '') + '_' + self.type)

    def for_match(self):
        """ sets 'contained_alias' ,'containing_alias', and 'containing_type_alias'  keyword arguments for an annotation """
        kwargs = {}
        kwargs['contained_alias'] = self.contained_annotation.alias
        kwargs['containing_alias'] = self.define_alias
        kwargs['containing_type_alias'] = self.define_type_alias
        if self.depth != 1:
            kwargs['depth'] = '*' + str(self.depth)
        else:
            kwargs['depth'] = ''
        return self.template.format(**kwargs)
