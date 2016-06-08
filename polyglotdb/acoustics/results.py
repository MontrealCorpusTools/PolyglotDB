

class Result(object):
    def items(self):
        """
        Generates sorted generator of times and F0 values
        """
        for k in sorted(self.track.keys()):
            yield (k,self.track[k])

    def keys(self):
        """
        Generates sorted generator of keys
        """
        for k in sorted(self.track.keys()):
            yield k

    def values(self):
        """
        Generates sorted generator of values
        """
        for k in sorted(self.track.keys()):
            yield self.track[k]

    def __getitem__(self, key):
        return self.track[key]

    def __iter__(self):
        for k in sorted(self.track.keys()):
            yield self.track[k]

    def max(self):
        """
        Returns
        -------
        max value (F0)
        """
        return max(self.values())

    def min(self):
        """
        Returns
        -------
        min value (F0)
        """

        return min(self.values())

    def average(self):
        """
        Returns
        -------
        average value (F0)
        """
        return sum(self.values()) / len(self.values())


class PitchResult(Result):
    def __init__(self, sql_results):
        """
        sets up dictionary where key is time and value is F0
        """
        self.track = {}
        for line in sql_results:
            self.track[line.time] = line.F0

class IntensityResult(Result):
    def __init__(self, sql_results):
        """
        sets up dictionary where key is time and value is intensity
        """
        self.track = {}
        for line in sql_results:
            self.track[line.time] = line.intensity

class FormantsResult(Result):
    def __init__(self, sql_results):
        """
        sets up dictionary where key is time and value tuple of formants
        """
        self.track = {}
        for line in sql_results:
            self.track[line.time] = (line.F1, line.F2, line.F3)

    def max(self):
        """
        Returns
        -------
        max value for formants
        """
        return (max(x[0] for x in self.values()), max(x[1] for x in self.values()),
                max(x[2] for x in self.values()))

    def min(self):
        """
        Returns
        -------
        min value for formants
        """
        return (min(x[0] for x in self.values()), min(x[1] for x in self.values()),
                min(x[2] for x in self.values()))

    def average(self):
        """
        Returns
        -------
        average value for formants
        """
        n = len(self.values())
        return (sum(x[0] for x in self.values()) / n, sum(x[1] for x in self.values()) / n,
                sum(x[2] for x in self.values()) / n)
