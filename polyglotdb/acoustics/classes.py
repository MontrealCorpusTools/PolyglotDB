class Track(object):
    def __init__(self):
        self.points = []

    def add(self, point):
        self.points.append(point)

    def __iter__(self):
        for p in sorted(self.points, key=lambda x: x.time):
            yield p

class TimePoint(object):
    def __init__(self, time):
        self.time = time
        self.values = {}

    def __getattr__(self, item):
        if item in self.values:
            return self.values[item]

    def add_value(self, name, value):
        self.values[name] = value