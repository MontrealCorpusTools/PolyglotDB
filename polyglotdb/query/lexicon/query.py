from ..base import BaseQuery


class LexiconQuery(BaseQuery):
    """
    Class for generating a Cypher query over the lexicon (type information about annotations in the corpus)
    """

    def __init__(self, corpus, to_find):
        super(LexiconQuery, self).__init__(corpus, to_find)

    def create_subset(self, label):
        """
        Create a type subset

        Parameters
        ----------
        label : str
            Name of the subset
        """
        labels_to_add = []
        if self.to_find.node_type not in self.corpus.hierarchy.subset_types or \
                label not in self.corpus.hierarchy.subset_types[self.to_find.node_type]:
            labels_to_add.append(label)
        super(LexiconQuery, self).create_subset(label)
        if labels_to_add:
            self.corpus.hierarchy.add_type_subsets(self.corpus, self.to_find.node_type, labels_to_add)
        self.corpus.encode_hierarchy()

    def remove_subset(self, label):
        """
        Delete a subset label from the corpus.

        N.B. This function only removes the type subset label, not any annotations or data in the corpus.

        Parameters
        ----------
        label : str
            Name of the subset to remove
        """

        super(LexiconQuery, self).remove_subset(label)
        self.corpus.hierarchy.remove_type_subsets(self.corpus, self.to_find.node_type, [label])

    def set_properties(self, **kwargs):
        """
        Set properties of the returned data.  Setting a property to ``None`` will result in it being deleted.

        Parameters
        ----------
        kwargs : kwargs
            Properties to set
        """
        props_to_remove = []
        props_to_add = []
        for k, v in kwargs.items():
            if v is None:
                props_to_remove.append(k)
            else:
                if not self.corpus.hierarchy.has_type_property(self.to_find.node_type, k):
                    props_to_add.append((k, type(kwargs[k])))
        super(LexiconQuery, self).set_properties(**kwargs)
        if props_to_add:
            self.corpus.hierarchy.add_type_properties(self.corpus, self.to_find.node_type, props_to_add)
        if props_to_remove:
            self.corpus.hierarchy.remove_type_properties(self.corpus, self.to_find.node_type, props_to_remove)
