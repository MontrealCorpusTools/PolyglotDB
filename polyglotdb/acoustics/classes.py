class Track(object):
    """
    Track class to contain, select, and manage :class:`~polyglotdb.acoustics.classes.TimePoint` objects

    Attributes
    ----------
    points : iterable of :class:`~polyglotdb.acoustics.classes.TimePoint`
        Time points with values of the acoustic track
    """
    def __init__(self):
        self.points = []

    def __str__(self):
        return '<Track: {}>'.format(self.points)

    def __repr__(self):
        return '<TrackObject with {} points'.format(len(self.points))

    def keys(self):
        """
        Get a list of all keys for TimePoints that the Track has

        Returns
        -------
        list
            All keys on TimePoint objects
        """
        keys = set()
        for point in self:
            keys.update(point.values.keys())
        return sorted(keys)

    def times(self):
        """
        Get a list of all time points in the track

        Returns
        -------
        list
            Sorted time points
        """
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
        """
        Add a :class:`~polyglotdb.acoustics.classes.TimePoint` to the track

        Parameters
        ----------
        point : :class:`~polyglotdb.acoustics.classes.TimePoint`
            Time point to add

        """
        self.points.append(point)

    def __iter__(self):
        for p in sorted(self.points, key=lambda x: x.time):
            yield p

    def items(self):
        """
        Generator for returning tuples of the time point and values

        Returns
        -------
        generator
            Tuples of time points and values
        """
        for p in sorted(self.points, key=lambda x: x.time):
            yield p.time, p.values

    def slice(self, begin, end):
        """
        Create a slice of the acoustic track between two times

        Parameters
        ----------
        begin : float
            Begin time for the slice
        end : float
            End time for the slice

        Returns
        -------
        :class:`~polyglotdb.acoustics.classes.Track`
            Track constructed from just the time points in the specified time
        """
        new_track = Track()
        for p in self:
            if p.time < begin:
                continue
            if p.time > end:
                break
            new_track.add(p)
        return new_track


class TimePoint(object):
    """
    Class for handling acoustic measurements at a specific time point

    Attributes
    ----------
    time : float
        The time of the time point
    values : dict
        Dictionary of acoustic measures for the given time point
    """
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
        """
        Check whether a time point contains a named measure

        Parameters
        ----------
        name : str
            Name of the measure

        Returns
        -------
        bool
            True if name is in values and has a value
        """
        return name in self.values and self.values[name] is not None

    def select_values(self, columns):
        """
        Generate a dictionary of only the specified measurement names

        Parameters
        ----------
        columns : iterable
            Iterable of measurement names to include

        Returns
        -------
        dict
            Subset of values if their name is in the specified columns

        """
        return {k: v for k,v in self.values.items() if k in columns}

    def add_value(self, name, value):
        """
        Add a new named measure and value to the TimePoint

        Parameters
        ----------
        name : str
            Name of the measure
        value : object
            Measure value

        """
        self.values[name] = value

    def update(self, point):
        """
        Update values in this time point from another TimePoint

        Parameters
        ----------
        point : :class:`polyglotdb.acoustics.classes.TimePoint`
            TimePoint to get values from

        """
        for k,v in point.values.items():
            self.values[k] = v
