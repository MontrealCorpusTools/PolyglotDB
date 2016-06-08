
from .base import BaseContext

from ..io.importer import (speaker_data_to_csvs, import_speaker_csvs,
                            discourse_data_to_csvs, import_discourse_csvs)

class SpokenContext(BaseContext):
    def enrich_speakers(self, speaker_data, type_data = None):
        """
        adds properties to speakers, adds speaker properties to census
        adds pproperties to hierarchy
        Parameters
        ----------
        speaker_data : dict
            the data about the speakers to add
        type_data : dict
            default to None
        
        """
        if type_data is None:
            type_data = {k: type(v) for k,v in next(iter(speaker_data.values())).items()}

        speakers = set(self.speakers)
        speaker_data = {k: v for k,v in speaker_data.items() if k in speakers}
        self.census.add_speaker_properties(speaker_data, type_data)
        speaker_data_to_csvs(self, speaker_data)
        import_speaker_csvs(self, type_data)
        self.hierarchy.add_speaker_properties(self, type_data.items())
        self.encode_hierarchy()

    def reset_speakers(self):
        pass

    def enrich_discourses(self, discourse_data, type_data = None):
        """
        adds properties to discourses, adds properties to census
        adds properties to hierarchy

        Parameters
        ----------
        discours_data : dict
            the data about the discourse to add
        type_data : dict
            default to None
        
        """
        if type_data is None:
            type_data = {k: type(v) for k,v in next(iter(discourse_data.values())).items()}

        discourses = set(self.discourses)
        discourse_data = {k: v for k,v in discourse_data.items() if k in discourses}
        self.census.add_discourse_properties(discourse_data, type_data)
        discourse_data_to_csvs(self, discourse_data)
        import_discourse_csvs(self, type_data)
        self.hierarchy.add_discourse_properties(self, type_data.items())
        self.encode_hierarchy()

    def reset_discourses(self):
        pass
