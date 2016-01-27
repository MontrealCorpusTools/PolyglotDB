
from ..helper import key_for_cypher

from .speaker import SpeakerAnnotation

class DiscourseAnnotation(SpeakerAnnotation):
    template = '''({token_alias})-[:spoken_in]->({discourse_alias})'''

    def __init__(self, contained_annotation, corpus = None):
        super(DiscourseAnnotation, self).__init__(contained_annotation, corpus)
        self.type = 'Discourse'

    def for_match(self):
        kwargs = {}
        kwargs['token_alias'] = self.contained_annotation.alias
        kwargs['discourse_alias'] = self.define_alias
        return self.template.format(**kwargs)
