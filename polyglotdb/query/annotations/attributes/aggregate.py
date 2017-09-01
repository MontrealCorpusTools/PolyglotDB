from .base import AnnotationAttribute, key_for_cypher


class AggregateAttribute(AnnotationAttribute):
    def __init__(self, aggregate):
        self.aggregate = aggregate

    @property
    def alias(self):
        """ returns annotation alias, label, and aggregate function turned into a cypher key format """
        return key_for_cypher('{}_{}_{}'.format(self.annotation.alias, self.label, self.aggregate.function))

    @property
    def annotation(self):
        """ Returns aggregate attribute annotation"""
        return self.aggregate.attribute.annotation

    @property
    def label(self):
        """ returns aggregate attribute label"""
        return self.aggregate.attribute.label

    @property
    def output_label(self):
        """ returns aggregate attribute output label """
        return self.aggregate.aliased_for_output()

    def for_with(self):
        """ Calls for_cypher() """
        return self.aggregate.for_cypher()

    def for_cypher(self):
        """ returns attribute output label """
        return self.output_label
