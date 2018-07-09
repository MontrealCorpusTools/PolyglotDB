class Track(object):
    def __init__(self):
        self.points = []

    def keys(self):
        keys = set()
        for point in self:
            keys.update(point.values.keys())
        return sorted(keys)

    def __getitem__(self, time):
        for point in self:
            if point.time == time:
                return point
        return None

    def __len__(self):
        return len(self.points)

    def __contains__(self, time):
        for point in self:
            if point.time == time:
                return True
        return False

    def add(self, point):
        self.points.append(point)

    def __iter__(self):
        for p in sorted(self.points, key=lambda x: x.time):
            yield p


class TimePoint(object):
    def __init__(self, time):
        self.time = time
        self.values = {}

    def __str__(self):
        return '<Time point {}: {}>'.format(self.time, self.values)

    def __contains__(self, item):
        return item in self.values

    def __getitem__(self, item):
        if item == 'time':
            return self.time
        return self.values[item]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __getattr__(self, item):
        if item in self.values:
            return self.values[item]

    def add_value(self, name, value):
        self.values[name] = value

    def update(self, point):
        for k,v in point.values.items():
            self.values[k] = v