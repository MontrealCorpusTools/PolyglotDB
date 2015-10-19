

class Result(object):
    def items(self):
        for k in sorted(self.track.keys()):
            yield (k,self.track[k])

    def keys(self):
        for k in sorted(self.track.keys()):
            yield k

    def values(self):
        for k in sorted(self.track.keys()):
            yield self.track[k]

    def __getitem__(self, key):
        return self.track[key]

    def __iter__(self):
        for k in sorted(self.track.keys()):
            yield self.track[k]


    def max(self):
        return max(self.values())

    def min(self):
        return max(self.values())

    def average(self):
        return sum(self.values()) / len(self.values())


class PitchResult(Result):
    def __init__(self, sql_results):
        self.track = {}
        for line in sql_results:
            self.track[line.time] = line.F0
