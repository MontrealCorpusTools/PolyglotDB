from ..base import Node, NodeAttribute

from ..base.helper import key_for_cypher

from ...exceptions import LexiconAttributeError, SubsetError


class LexiconAttribute(NodeAttribute):
    pass


class LexiconNode(Node):
    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, LexiconNode):
            return False
        if self.key != other.key:
            return False
        return True

    @property
    def alias(self):
        return key_for_cypher(self.alias_template.format(t='type_'+self.key))

    @property
    def define_alias(self):
        """ Returns a cypher string for getting all type_labels"""
        label_string = ':{}_type'.format(self.node_type)
        if self.corpus is not None:
            label_string += ':{}'.format(key_for_cypher(self.corpus))
        if self.subset_labels:
            subset_type_labels = [x for x in self.subset_labels if self.hierarchy.has_type_subset(self.node_type, x)]
            if subset_type_labels:
                label_string += ':' + ':'.join(map(key_for_cypher, subset_type_labels))
        return '{}{}'.format(self.alias, label_string)

    def __getattr__(self, key):
        if self.hierarchy is not None and not self.hierarchy.has_type_property(
                self.node_type, key):
            properties = [x[0] for x in
                          self.hierarchy.type_properties[self.node_type]]
            raise LexiconAttributeError(
                'The \'{}\' annotation types do not have a \'{}\' property in the lexicon (available: {}).'.format(
                    self.node_type,
                    key, ', '.join(
                        properties)))
        return LexiconAttribute(self, key)

    def filter_by_subset(self, *args):
        """ adds each item in args to the hierarchy type_labels"""
        if self.hierarchy is not None:
            for a in args:
                if not self.hierarchy.has_type_subset(self.node_type, a):
                    raise (SubsetError('{} is not a subset of {} types.'.format(a, self.node_type)))
        self.subset_labels = sorted(set(self.subset_labels + list(args)))
        return self
