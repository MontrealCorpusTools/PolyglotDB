
from ..types.standardized import PGAnnotation, PGSubAnnotation, PGAnnotationType

from ..types.parsing import Tobi, BreakIndex

from ..discoursedata import DiscourseData

from ...exceptions import ParseError


class BaseParser(object):
    """
    Base parser, extend this class for new parsers.

    Parameters
    ----------
    annotation_tiers: list
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
    """
    _extensions = ['.txt']

    def __init__(self, annotation_tiers, hierarchy, make_transcription=True,
                 make_label=False,
                 stop_check=None, call_back=None):
        self.speaker_parser = None
        self.annotation_tiers = annotation_tiers
        self.hierarchy = hierarchy
        self.make_transcription = make_transcription
        self.make_label = make_label
        self.stop_check = stop_check
        self.call_back = call_back

    def match_extension(self, filename):
        """
        Ensures that filename ends with acceptable extension

        Parameters
        ----------
        filename : str
            the filename of the file being checked

        Returns
        -------
        boolean
            True if filename is acceptable extension, false otherwise
        """
        for x in self._extensions:
            if filename.lower().endswith(x):
                break
        else:
            return False
        return True

    def _parse_annotations(self, types_only=False):
        annotation_tiers = {}
        segment_type = None
        for k, v in self.hierarchy.items():
            annotation_tiers[k] = PGAnnotationType(k)
            annotation_tiers[k].supertype = v
            if 'word' in k:
                annotation_tiers[k].is_word = True  # FIXME?
                self.hierarchy.type_properties['word'] = set()
                self.hierarchy.token_properties['word'] = set()
            if k not in self.hierarchy.values() and not annotation_tiers[k].is_word:
                segment_type = k

        for k in annotation_tiers.keys():
            relevent_levels = {}
            lengths = {}
            for inputlevel in self.annotation_tiers:
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
                    raise (
                    ParseError('Annotations sharing a linguistic type and a speaker don\'t have a consistent length.'))
            for speaker, speaker_levels in relevent_levels.items():
                for i in range(lengths[speaker]):
                    type_properties = {}
                    token_properties = {}
                    label = None
                    begin = None
                    end = None
                    for rl in speaker_levels:
                        if types_only and not rl.type_property:
                            annotation_tiers[k].token_property_keys.add(rl.name)
                            continue
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
                        if rl.name == k or rl.name == 'label' or rl.label:
                            if rl[i].value == '':
                                label = '<SIL>'
                            elif rl[i].value is not None:
                                label = rl[i].value
                        elif rl.type_property:
                            if False and not types_only:
                                print(rl.name, 'is type!')
                            type_properties[rl.name] = rl[i].value
                        else:
                            if False and not types_only:
                                print(rl.name, 'is token!')
                            token_properties[rl.name] = rl[i].value
                    a = PGAnnotation(label, begin, end)
                    a.type_properties.update(type_properties)
                    a.token_properties.update(token_properties)
                    a.speaker = speaker
                    if i != 0:
                        a.previous_id = annotation_tiers[k][-1].id
                    annotation_tiers[k].add(a)
                for rl in speaker_levels:
                    if types_only:
                        continue
                    if not rl.subannotation:
                        continue
                    for sub in rl:
                        #TODO: Maybe will cause VOTs to be under wrong phone.
                        annotation = annotation_tiers[k].lookup(sub.midpoint, speaker=speaker)
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
        for k, v in annotation_tiers.items():
            annotation_tiers[k].optimize_lookups()
            if not types_only:
                st = v.supertype
                if st is not None:
                    annotation_tiers[st].optimize_lookups()
                    for a in annotation_tiers[k]:
                        super_annotation = annotation_tiers[st].lookup(a.midpoint, speaker=a.speaker)
                        try:
                            a.super_id = super_annotation.id
                        except AttributeError:
                            pass
                            # raise
            if self.make_transcription and segment_type is not None and v.is_word:
                v.type_property_keys.update(['transcription'])
                annotation_tiers[segment_type].optimize_lookups()
                for a in annotation_tiers[k]:
                    transcription = annotation_tiers[segment_type].lookup_range(a.begin, a.end, speaker=a.speaker)
                    a.type_properties['transcription'] = [x.label for x in transcription]
                v.type_properties |= set([(tuple(['transcription', type("string")]))])
                self.hierarchy.type_properties['word'] |= set([(tuple(['transcription', type("string")]))])
            if self.make_label and 'transcription' in v.type_property_keys and v.is_word:
                for a in annotation_tiers[k]:
                    if a.label is None:
                        a.label = ''.join(a.type_properties['transcription'])
                        annotation_tiers[k].type_property_keys.add('label')
                        annotation_tiers[k].token_property_keys.add('label')
        return annotation_tiers

    def parse_information(self, path, corpus_name):
        """
        Parses types out of a corpus

        Parameters
        ----------
        path : str
            a path to the corpus
        corpus_name : str
            name of the corpus

        Returns
        -------
        data.types : list
            a list of data types
        """
        data = self.parse_discourse(path, types_only=True)
        return_dict = {}
        return_dict['types'], return_dict['type_headers'] = data.types(corpus_name)
        return_dict['token_headers'] = data.token_headers
        return_dict['subannotations'] = data.hierarchy.subannotations
        return_dict['speakers'] = data.speakers
        return return_dict

    def parse_discourse(self, name, types_only=False):
        """
        Parse annotations for later importing.

        Parameters
        ----------
        name : str
            Name of the discourse
        types_only : bool
            Flag for whether to only save type information, ignoring the token information

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data
        """

        pg_annotations = self._parse_annotations(types_only)
        data = DiscourseData(name, pg_annotations, self.hierarchy)
        return data
