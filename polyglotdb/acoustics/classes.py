class Track(object):
    def __init__(self):
        self.points = []

    def __str__(self):
        return '<Track: {}>'.format(self.points)

    def __repr__(self):
        return '<TrackObject with {} points'.format(len(self.points))

    def keys(self):
        keys = set()
        for point in self:
            keys.update(point.values.keys())
        return sorted(keys)

    def times(self):
        times = set()
        for point in self:
            times.add(point.time)
        return sorted(times)

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

    def slice(self, begin, end):
        new_track = Track()
        for p in self:
            if p.time < begin:
                continue
            if p.time > end:
                break
            new_track.add(p)
        return new_track


class TimePoint(object):
    def __init__(self, time):
        self.time = time
        self.values = {}

    def __str__(self):
        return '<Time point {}: {}>'.format(self.time, self.values)

    def __repr__(self):
        return str(self)

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

    def has_value(self, name):
        return name in self.values and self.values[name] is not None

    def select_values(self, columns):
        return {k: v for k,v in self.values.items() if k in columns}

    def add_value(self, name, value):
        self.values[name] = value

    def update(self, point):
        for k,v in point.values.items():
            self.values[k] = v