
from .base import BaseAnnotationType, BaseAnnotation

class IntervalAnnotation(BaseAnnotation):
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

class PointAnnotation(BaseAnnotation):
    def __init__(self, time):
        self.time = time

class IntervalAnnotationType(BaseAnnotationType):
    pass

class PointAnnotationType(BaseAnnotationType):
    pass
