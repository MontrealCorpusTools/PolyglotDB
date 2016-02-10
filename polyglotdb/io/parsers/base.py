import os

from ..types.standardized import PGAnnotation, PGSubAnnotation, PGAnnotationType

from ..types.parsing import Tobi, BreakIndex

from ..discoursedata import DiscourseData

class BaseParser(object):
    '''
    Base parser, extend this class for new parsers.

    Parameters
    ----------
    annotation_types: list
        Annotation types of the files to parse
    hierarchy : :class:`~polyglotdb.structure.Hierarchy`
        Details of how linguistic types relate to one another
    make_transcription : bool, defaults to True
        If true, create a word attribute for transcription based on segments
        that are contained by the word
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    '''
    _extensions = ['.txt']
    def __init__(self, annotation_types, hierarchy, make_transcription = True,
                    make_label = False,
                    stop_check = None, call_back = None):
        self.speaker_parser = None
        self.annotation_types = annotation_types
        self.hierarchy = hierarchy
        self.make_transcription = make_transcription
        self.make_label = make_label
        self.stop_check = stop_check
        self.call_back = call_back

    def match_extension(self, filename):
        for x in self._extensions:
            if filename.lower().endswith(x):
                break
        else:
            return False
        return True

    def _parse_annotations(self):
        annotation_types = {}
        segment_type = None
        for k, v in self.hierarchy.items():
            annotation_types[k] = PGAnnotationType(k)
            annotation_types[k].supertype = v
            if 'word' in k:
                annotation_types[k].is_word = True # FIXME?
            if k not in self.hierarchy.values() and not annotation_types[k].is_word:
                segment_type = k

        for k in annotation_types.keys():
            relevent_levels = {}
            lengths = {}
            for inputlevel in self.annotation_types:
                if inputlevel.ignored:
                    continue
                if inputlevel.linguistic_type != k:
                    continue
                speaker = inputlevel.speaker
                if speaker not in relevent_levels:
                    relevent_levels[speaker] = []
                if speaker not in lengths:
                    lengths[speaker] = 0
                relevent_levels[speaker].append(inputlevel)
                if inputlevel.subannotation:
                    continue
                if lengths[speaker] == 0:
                    lengths[speaker] = len(inputlevel)
                elif lengths[speaker] != len(inputlevel):
                    raise(Exception('Annotations sharing a linguistic type and a speaker don\'t have a consistent length.'))
            for speaker, speaker_levels in relevent_levels.items():
                for i in range(lengths[speaker]):
                    type_properties = {}
                    token_properties = {}
                    label = None
                    begin = None
                    end = None
                    for rl in speaker_levels:
                        if rl.subannotation:
                            continue
                        if begin is None:
                            try:
                                begin = rl[i].begin
                            except AttributeError:
                                try:
                                    begin = rl[i].time
                                except AttributeError:
                                    pass
                        if end is None:
                            try:
                                end = rl[i].end
                            except AttributeError:
                                try:
                                    end = rl[i].time
                                except AttributeError:
                                    pass
                        if rl.name == k or rl.name == 'label':
                            if rl[i].value == '':
                                label = '<SIL>'
                            elif rl[i].value is not None:
                                label = rl[i].value
                        elif rl.type_property:
                            type_properties[rl.name] = rl[i].value
                        else:
                            token_properties[rl.name] = rl[i].value

                    a = PGAnnotation(label, begin, end)
                    a.type_properties.update(type_properties)
                    a.token_properties.update(token_properties)
                    a.speaker = speaker
                    if i != 0:
                        a.previous_id = annotation_types[k][-1].id
                    annotation_types[k].add(a)
                for rl in speaker_levels:
                    if not rl.subannotation:
                        continue
                    for sub in rl:

                        annotation = annotation_types[k].lookup(sub.midpoint, speaker = speaker)
                        if isinstance(sub, Tobi):
                            a = PGSubAnnotation(sub.label, 'tone', sub.begin, sub.end)
                        elif isinstance(sub, BreakIndex):
                            a = PGSubAnnotation(sub.value, 'break', sub.begin, sub.end)
                        else:
                            a = PGSubAnnotation(None, sub.label, sub.begin, sub.end)
                        annotation.subannotations.append(a)
                        if k not in self.hierarchy.subannotations:
                            self.hierarchy.subannotations[k] = set()
                        self.hierarchy.subannotations[k].add(a.type)

        for k, v in annotation_types.items():
            st = v.supertype
            if st is not None:
                for a in annotation_types[k]:
                    super_annotation = annotation_types[st].lookup(a.midpoint, speaker = a.speaker)
                    a.super_id = super_annotation.id
            if self.make_transcription and segment_type is not None and v.is_word:
                v.type_property_keys.update(['transcription'])
                for a in annotation_types[k]:
                    transcription = annotation_types[segment_type].lookup_range(a.begin, a.end, speaker = a.speaker)
                    a.type_properties['transcription'] = [x.label for x in transcription]
            if self.make_label and 'transcription' in v.type_property_keys and v.is_word:
                for a in annotation_types[k]:
                    if a.label is None:
                        a.label = ''.join(a.type_properties['transcription'])
                        annotation_types[k].type_property_keys.add('label')
                        annotation_types[k].token_property_keys.add('label')
        return annotation_types


    def parse_discourse(self, name):
        '''
        Parse annotations for later importing.

        Parameters
        ----------
        name : str
            Name of the discourse

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data
        '''
        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        return data
