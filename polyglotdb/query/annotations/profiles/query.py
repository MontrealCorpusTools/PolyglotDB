from .base import BaseProfile


class ProfileMatchError(Exception):
    pass


class QueryProfile(BaseProfile):
    extension = '.queryprofile'

    def __init__(self):
        self.filters = []
        self.name = ''
        self.to_find = None

    def valid_profile(self, corpus_context):
        try:
            self.for_polyglot(corpus_context)
        except AttributeError:
            return False
        return True

    def for_polyglot(self, corpus_context):
        return [x.for_polyglot(corpus_context) for x in self.filters]
