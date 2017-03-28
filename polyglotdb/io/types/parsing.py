from .form import (PointAnnotation, PointAnnotationType, IntervalAnnotation,
                   IntervalAnnotationType)

from .content import (OrthographyAnnotation, OrthographyAnnotationType,
                      TranscriptionAnnotation, TranscriptionAnnotationType,
                      NumericAnnotation, NumericAnnotationType,
                      GroupingAnnotation, GroupingAnnotationType,
                      MorphemeAnnotation, MorphemeAnnotationType)


class Tobi(OrthographyAnnotation, PointAnnotation):
    def __init__(self, label, time):
        OrthographyAnnotation.__init__(self, label)
        PointAnnotation.__init__(self, time)


class TobiTier(OrthographyAnnotationType, PointAnnotationType):
    annotation_class = Tobi


class Orthography(OrthographyAnnotation, IntervalAnnotation):
    def __init__(self, label, begin, end):
        OrthographyAnnotation.__init__(self, label)
        IntervalAnnotation.__init__(self, begin, end)


class OrthographyTier(OrthographyAnnotationType, IntervalAnnotationType):
    annotation_class = Orthography


class Morpheme(MorphemeAnnotation, IntervalAnnotation):
    def __init__(self, morphemes, begin, end):
        MorphemeAnnotation.__init__(self, morphemes)
        IntervalAnnotation.__init__(self, begin, end)


class MorphemeTier(MorphemeAnnotationType, IntervalAnnotationType):
    annotation_class = Morpheme


class Transcription(TranscriptionAnnotation, IntervalAnnotation):
    def __init__(self, segments, begin, end, morpheme_breaks=None, stress=None, tone=None):
        TranscriptionAnnotation.__init__(self, segments, morpheme_breaks, stress, tone)
        IntervalAnnotation.__init__(self, begin, end)


class TranscriptionTier(TranscriptionAnnotationType, IntervalAnnotationType):
    annotation_class = Transcription


class Segment(Orthography):
    pass


class SegmentTier(IntervalAnnotationType, OrthographyAnnotationType):
    annotation_class = Segment


class Grouping(IntervalAnnotation, GroupingAnnotation):
    def __init__(self, begin, end):
        IntervalAnnotation.__init__(self, begin, end)


class GroupingTier(GroupingAnnotationType, IntervalAnnotationType):
    annotation_class = Grouping

    def add(self, annotations, save=True):
        for a in annotations:
            if len(a) > 2:
                label = a.pop(0)
            if save or len(self._list) < 10:
                # If save is False, only the first 10 annotations are saved
                annotation = self.annotation_class(*a)
                self._list.append(annotation)


class TextOrthography(OrthographyAnnotation, PointAnnotation):
    def __init__(self, label, time):
        OrthographyAnnotation.__init__(self, label)
        PointAnnotation.__init__(self, time)


class TextOrthographyTier(OrthographyAnnotationType, PointAnnotationType):
    annotation_class = TextOrthography


class TextMorpheme(MorphemeAnnotation, PointAnnotation):
    def __init__(self, morphemes, time):
        MorphemeAnnotation.__init__(self, morphemes)
        PointAnnotation.__init__(self, time)


class TextMorphemeTier(MorphemeAnnotationType, PointAnnotationType):
    annotation_class = TextMorpheme


class TextTranscription(TranscriptionAnnotation, PointAnnotation):
    def __init__(self, segments, time, morpheme_breaks=None, stress=None, tone=None):
        TranscriptionAnnotation.__init__(self, segments, morpheme_breaks, stress, tone)
        PointAnnotation.__init__(self, time)


class TextTranscriptionTier(TranscriptionAnnotationType, PointAnnotationType):
    annotation_class = TextTranscription


class BreakIndex(NumericAnnotation, PointAnnotation):
    def __init__(self, value, time):
        NumericAnnotation.__init__(self, value)
        PointAnnotation.__init__(self, time)


class BreakIndexTier(NumericAnnotationType, PointAnnotationType):
    annotation_class = BreakIndex
