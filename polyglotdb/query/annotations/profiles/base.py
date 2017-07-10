import os
import pickle
from polyglotdb.config import BASE_DIR

PROFILE_DIR = os.path.join(BASE_DIR, 'profiles')
os.makedirs(PROFILE_DIR, exist_ok=True)


class Filter(object):
    def __init__(self, attribute, operator, value):
        self.attribute = attribute
        self.operator = operator
        self.value = value

    def __repr__(self):
        return '<Filter {}, {}, {}>'.format(self.attribute, self.operator, self.value)

    @property
    def is_alignment(self):
        if self.attribute[-1] not in ['begin', 'end']:
            return False
        if not isinstance(self.value, tuple):
            return False
        if self.attribute[-1] != self.value[-1]:
            return False
        if self.operator not in ['==', '!=']:
            return False
        return True

    def for_polyglot(self, corpus_context):
        att = corpus_context
        attribute = self.attribute
        if isinstance(attribute[0], (tuple, list)):
            attribute = attribute[0]
        for a in attribute:
            if a == '':
                continue
            if a.endswith('_name'):
                att = getattr(att, getattr(corpus_context, a))
            else:
                att = getattr(att, a)

        if isinstance(self.value, tuple):
            value = corpus_context
            for a in self.value:
                if a == '':
                    continue
                if a.endswith('_name'):
                    value = getattr(value, getattr(corpus_context, a))
                else:
                    value = getattr(value, a)

        else:
            value = self.value

        boolValue = False
        if type(value) == bool and value:
            boolValue = True

        if self.operator in ['==','=']:
            return att == value
        elif self.operator in ['!=', '<>']:
            if boolValue:
                return att == None
            return att != value
        elif self.operator == '>':
            return att > value
        elif self.operator == '>=':
            return att >= value
        elif self.operator == '<':
            return att < value
        elif self.operator == '<=':
            return att <= value
        elif self.operator.lower() == 'in':
            return att.in_(value)
        elif self.operator.lower() == 'not in':
            return att.not_in_(value)
        elif self.operator.lower() in ['regex', '=~']:
            return att.regex(value)


class Column(object):
    def __init__(self, attribute, name):
        self.attribute = attribute
        self.name = name

    def for_polyglot(self, corpus_context, to_find):
        att = corpus_context.hierarchy
        if 'speaker' in self.attribute:
            ind = self.attribute.index('speaker')
            att = getattr(corpus_context, to_find)
            for a in self.attribute[ind:]:
                att = getattr(att, a)
        elif 'discourse' in self.attribute:
            ind = self.attribute.index('discourse')
            att = getattr(corpus_context, to_find)
            for a in self.attribute[ind:]:
                att = getattr(att, a)
        else:
            if self.attribute[0] != to_find:
                att = getattr(corpus_context, to_find)
            for a in self.attribute:
                if a.endswith('_name'):
                    att = getattr(att, getattr(corpus_context, a))
                else:
                    att = getattr(att, a)
        att = att.column_name(self.name)
        return att

    def __repr__(self):
        return '<Column {}, {}>'.format(self.attribute, self.name)


class BaseProfile(object):
    extension = ''

    def __init__(self):
        self.name = ''

    @property
    def path(self):
        return os.path.join(PROFILE_DIR, self.name.replace(' ', '_') + self.extension)

    @classmethod
    def load_profile(cls, name):
        path = os.path.join(PROFILE_DIR, name.replace(' ', '_') + cls.extension)
        with open(path, 'rb') as f:
            obj = pickle.load(f)
        return obj

    def save_profile(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self, f)
