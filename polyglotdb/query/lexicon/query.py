from ..base import BaseQuery

from .cypher import query_to_cypher


class LexiconQuery(BaseQuery):
    def __init__(self, corpus, to_find):
        super(LexiconQuery, self).__init__(corpus, to_find)

    def create_subset(self, label):
        """
        Set properties of the returned tokens.
        """
        self._set_labels.append(label)

        labels_to_add = []
        if self.to_find.node_type not in self.corpus.hierarchy.subset_types or \
                        label not in self.corpus.hierarchy.subset_types[self.to_find.node_type]:
            labels_to_add.append(label)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        if labels_to_add:
            self.corpus.hierarchy.add_type_labels(self.corpus, self.to_find.node_type, labels_to_add)
        self.corpus.encode_hierarchy()
        self._set_labels = []

    def remove_subset(self, label):
        """ removes all token labels"""
        self._remove_labels.append(label)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

        self.corpus.hierarchy.remove_type_labels(self.corpus, self.to_find.node_type, self._remove_labels)
        self._remove_labels = []

    def set_properties(self, **kwargs):
        """
        Set properties of the returned tokens.
        """
        props_to_remove = []
        props_to_add = []
        for k, v in kwargs.items():
            if v is None:
                props_to_remove.append(k)
            else:
                self._set_properties[k] = v
                if not self.corpus.hierarchy.has_type_property(self.to_find.node_type, k):
                    props_to_add.append((k, type(kwargs[k])))

        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        if props_to_add:
            self.corpus.hierarchy.add_type_properties(self.corpus, self.to_find.node_type, props_to_add)
        if props_to_remove:
            self.corpus.hierarchy.remove_type_properties(self.corpus, self.to_find.node_type, props_to_remove)
        self._set_properties = {}

    def cypher(self):
        """
        Generates a Cypher statement based on the query.
        """
        return query_to_cypher(self)
