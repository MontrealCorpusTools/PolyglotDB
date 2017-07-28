from .base import BaseProfile


class ExportProfile(BaseProfile):
    extension = '.exportprofile'

    def __init__(self):
        self.columns = []
        self.name = ''
        self.to_find = None

    def for_polyglot(self, corpus_context, to_find=None):
        columns = []
        if to_find is None:
            to_find = self.to_find
        for x in self.columns:
            try:
                columns.append(x.for_polyglot(corpus_context, to_find))
            except AttributeError:
                pass
        return columns
