
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
    template = '''filter(x in nodes({path}) WHERE (x)-[:is_a]->({type} {{{label}: {value}}}))'''
    #template = "{value} in extract(x in nodes({path})| x.{label})"
    def for_cypher(self):
        kwargs = {'path':self.attribute.annotation.alias,
                'value':value_for_cypher(self.value),
                'label': key_for_cypher(self.attribute.label),
                'type': ':{}_type'.format(self.attribute.annotation.type)}
        return self.template.format(**kwargs)

class AlignmentClauseElement(ClauseElement):
    template = "{first}.label = {second}.label"
    side = ''
    def __init__(self, first, second):
        self.first = first
        self.second = second

    @property
    def annotations(self):
        return [self.first]

    def for_cypher(self):
        kwargs = {'first_rel_type': self.first.rel_type_alias,
                'second_rel_type': self.second.rel_type_alias,
                'node_alias': getattr(self.first, self.alias_to_use)}
        return self.template.format(**kwargs)

class RightAlignedClauseElement(AlignmentClauseElement):
    template = '''()-[:{first_rel_type}]->({node_alias})<-[:{second_rel_type}]-()'''
    alias_to_use = 'end_alias'

class LeftAlignedClauseElement(AlignmentClauseElement):
    template = '''()<-[:{first_rel_type}]-({node_alias})-[:{second_rel_type}]->()'''
    alias_to_use = 'begin_alias'

class NotRightAlignedClauseElement(RightAlignedClauseElement):
    template = '''not ()-[:{first_rel_type}]->({node_alias})<-[:{second_rel_type}]-()'''

class NotLeftAlignedClauseElement(LeftAlignedClauseElement):
    template = '''not ()<-[:{first_rel_type}]-({node_alias})-[:{second_rel_type}]->()'''

