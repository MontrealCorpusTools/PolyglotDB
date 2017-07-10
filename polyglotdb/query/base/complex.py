

class ComplexClause(object):
    type_string = ''

    def __init__(self, *args):
        self.clauses = args
        self.add_prefix(self.type_string)

    def is_matrix(self):
        for c in self.clauses:
            if not c.is_matrix():
                return False
        return True

    def involves(self, annotation):
        for c in self.clauses:
            if c.involves(annotation):
                return True
        return False

    @property
    def nodes(self):
        """
        Get all annotations involved in the clause.
        """
        nodes = []
        for a in self.clauses:
            nodes.extend(a.nodes)
        return nodes

    @property
    def in_subquery(self):
        for a in self.clauses:
            if a.in_subquery:
                return True
        return False

    @property
    def attributes(self):
        """
        Get all attributes involved in the clause.
        """
        attributes = []
        for a in self.clauses:
            attributes.extend(a.attributes)
        return attributes

    def add_prefix(self, prefix):
        """
        Adds a prefix to a clause

        Parameters
        ----------
        prefix : str
            the prefix to add
        """
        for i, c in enumerate(self.clauses):
            if isinstance(c, ComplexClause):
                c.add_prefix(prefix + str(i))
            else:
                try:
                    c.value_alias_prefix += prefix + str(i)
                except AttributeError:
                    pass

    def generate_params(self):
        """
        Generates dictionary of parameters of ComplexClause

        Returns
        -------
        params : dict
            a dictionary of parameters
        """
        from .attributes import NodeAttribute
        params = {}
        for c in self.clauses:
            if isinstance(c, ComplexClause):
                params.update(c.generate_params())
            else:
                try:
                    if not isinstance(c.value, NodeAttribute):
                        params[c.cypher_value_string()[1:-1].replace('`', '')] = c.value
                except AttributeError:
                    pass
        return params


class or_(ComplexClause):
    type_string = 'or_'

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        temp = ' OR '.join(x.for_cypher() for x in self.clauses)
        temp = "(" + temp + ")"
        return temp


class and_(ComplexClause):
    type_string = 'and_'

    def for_cypher(self):
        """
        Return a Cypher representation of the clause.
        """
        temp = ' AND '.join(x.for_cypher() for x in self.clauses)
        temp = "(" + temp + ")"
        return temp