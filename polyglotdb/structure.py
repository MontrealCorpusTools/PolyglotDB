

class Hierarchy(object):
    def __init__(self, data = None):
        if data is None:
            data = {}
        self._data = data
        self.subannotations = {}

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, item):
        return item in self._data

    def update(self, other):
        self._data.update(other._data)
        self.subannotations.update(other.subannotations)
