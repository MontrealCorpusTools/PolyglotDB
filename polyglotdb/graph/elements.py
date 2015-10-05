
from .helper import key_for_cypher, value_for_cypher

class ClauseElement(object):
    sign = ''
    template = "{} {} {}"
    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    @property
    def annotations(self):
        annotations = [self.attribute.annotation]
        try:
            annotations.append(self.value.annotation)
        except AttributeError:
            pass
        return annotations

    def for_cypher(self):
        try:
            value = self.value.for_cypher()
        except AttributeError:
            value = value_for_cypher(self.value)
        return self.template.format(self.attribute.for_cypher(),
                                self.sign,
                                value)

class EqualClauseElement(ClauseElement):
    sign = '='

class GtClauseElement(ClauseElement):
    sign = '>'

class GteClauseElement(ClauseElement):
    sign = '>='

class LtClauseElement(ClauseElement):
    sign = '<'

class LteClauseElement(ClauseElement):
    sign = '<='

class NotEqualClauseElement(ClauseElement):
    sign = '<>'

class InClauseElement(ClauseElement):
    sign = 'IN'

class RegexClauseElement(ClauseElement):
    sign = '=~'

class ContainsClauseElement(ClauseElement):
    template = "{} in extract(x in nodes({})| x.{})"
    def for_cypher(self):
        return self.template.format(value_for_cypher(self.value),
                                                self.attribute.annotation.alias,
                                                key_for_cypher(self.attribute.label))

class AlignmentClauseElement(ClauseElement):
    template = "{first}.label = {second}.label"
    side = ''
    def __init__(self, first, second):
        self.first = first
        self.second = second

    @property
    def annotations(self):
        return [self.first, self.second]

    def for_cypher(self):
        if self.side == 'left':
            first = self.first.begin_alias
            second = self.second.begin_alias
        elif self.side == 'right':
            first = self.first.end_alias
            second = self.second.end_alias
        else:
            raise(NotImplementedError)
        return self.template.format(first = first,
                                second = second)

class RightAlignedClauseElement(AlignmentClauseElement):
    side = 'right'

class LeftAlignedClauseElement(AlignmentClauseElement):
    side = 'left'
