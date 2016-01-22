
from ..helper import key_for_cypher

from .base import Attribute

class AggregateAttribute(Attribute):
    def __init__(self, aggregate):
        self.aggregate = aggregate

    @property
    def alias(self):
        return key_for_cypher('{}_{}_{}'.format(self.annotation.alias, self.label, self.aggregate.function))

    @property
    def annotation(self):
        return self.aggregate.attribute.annotation

    @property
    def label(self):
        return self.aggregate.attribute.label

    @property
    def output_label(self):
        return self.aggregate.aliased_for_output()

    def for_with(self):
        return self.aggregate.for_cypher()

    def for_cypher(self):
        return self.output_label
