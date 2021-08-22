from ..io.importer import (speaker_data_to_csvs, import_speaker_csvs,
                           discourse_data_to_csvs, import_discourse_csvs)
from .audio import AudioContext
from ..io.enrichment.spoken import enrich_speakers_from_csv, enrich_discourses_from_csv, parse_file


class SpokenContext(AudioContext):
    """
    Class that contains methods for dealing specifically with speaker and sound file metadata
    """

    def enrich_speakers_from_csv(self, path):
        """
        Enriches speakers from a csv file

        Parameters
        ----------
        path : str
            the path to the csv file
        """
        enrich_speakers_from_csv(self, path)

    def reset_speaker_csv(self, path):
        """
        Remove properties that were encoded via a CSV file

        Parameters
        ----------
        path : str
            CSV file to get property names from
        """
        data, type_data = parse_file(path, [])
        q = self.query_speakers()
        property_names = [x for x in type_data.keys()]
        q.set_properties(**{x: None for x in property_names})

        self.hierarchy.remove_speaker_properties(self, property_names)
        self.encode_hierarchy()

    def reset_discourse_csv(self, path):
        """
        Remove properties that were encoded via a CSV file

        Parameters
        ----------
        path : str
            CSV file to get property names from
        """
        data, type_data = parse_file(path, [])
        q = self.query_discourses()
        property_names = [x for x in type_data.keys()]
        q.set_properties(**{x: None for x in property_names})
        self.hierarchy.remove_discourse_properties(self, property_names)
        self.encode_hierarchy()

    def enrich_discourses_from_csv(self, path):
        """
        Enriches discourses from a csv file

        Parameters
        ----------
        path : str
            the path to the csv file
        """
        enrich_discourses_from_csv(self, path)

    def get_speakers_in_discourse(self, discourse):
        """
        Get a list of all speakers that spoke in a given discourse

        Parameters
        ----------
        discourse : str
            Audio file to query over

        Returns
        -------
        list
            All speakers who spoke in the discourse
        """
        query = '''MATCH (d:Discourse:{corpus_name})<-[:speaks_in]-(s:Speaker:{corpus_name})
                WHERE d.name = $discourse_name
                RETURN s.name as speaker'''.format(corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(query, discourse_name=discourse)
        speakers = [x['speaker'] for x in results]
        return speakers

    def get_discourses_of_speaker(self, speaker):
        """
        Get a list of all discourses that a given speaker spoke in

        Parameters
        ----------
        speaker : str
            Speaker to query over

        Returns
        -------
        list
            All discourses the speaker spoke in
        """
        query = '''MATCH (d:Discourse:{corpus_name})<-[:speaks_in]-(s:Speaker:{corpus_name})
                WHERE s.name = $speaker_name
                RETURN d.name as discourse'''.format(corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(query, speaker_name=speaker)
        discourses = [x['discourse'] for x in results]
        return discourses

    def get_channel_of_speaker(self, speaker, discourse):
        """
        Get the channel that the speaker is in

        Parameters
        ----------
        speaker : str
            Speaker to query
        discourse : str
            Discourse to query

        Returns
        -------
        int
            Channel of audio that speaker is in
        """
        query = '''MATCH (d:Discourse:{corpus_name})<-[r:speaks_in]-(s:Speaker:{corpus_name})
                WHERE s.name = $speaker_name AND d.name = $discourse_name
                RETURN r.channel as channel'''.format(corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(query, speaker_name=speaker, discourse_name=discourse)
        return results[0]['channel']

    def enrich_speakers(self, speaker_data, type_data=None):
        """
        Add properties about speakers to the corpus, allowing them to
        be queryable.

        Parameters
        ----------
        speaker_data : dict
            the data about the speakers to add
        type_data : dict
            Specifies the type of the data to be added, defaults to None

        """
        if type_data is None:
            type_data = {k: type(v) for k, v in next(iter(speaker_data.values())).items()}
        speakers = set(self.speakers)
        speaker_data = {k: v for k, v in speaker_data.items() if k in speakers}

        speaker_data_to_csvs(self, speaker_data)
        import_speaker_csvs(self, type_data)
        self.hierarchy.add_speaker_properties(self, type_data.items())
        self.encode_hierarchy()

    def make_speaker_annotations_dict(self, data, speaker, property):
        """
        helper function to turn dict of {} format to {speaker :{property :{data}}}

        Parameters
        ----------
        data : dict
            annotations and values
        property : str
            the name of the property being encoded
        speaker : str
            the name of the speaker
        """
        return {speaker: {property: data}}

    def enrich_discourses(self, discourse_data, type_data=None):
        """
        Add properties about discourses to the corpus, allowing them to
        be queryable.

        Parameters
        ----------
        discourse_data : dict
            the data about the discourse to add
        type_data : dict
            Specifies the type of the data to be added, defaults to None

        """
        if type_data is None:
            type_data = {k: type(v) for k, v in next(iter(discourse_data.values())).items()}

        discourses = set(self.discourses)
        discourse_data = {k: v for k, v in discourse_data.items() if k in discourses}
        discourse_data_to_csvs(self, discourse_data)
        import_discourse_csvs(self, type_data)
        self.hierarchy.add_discourse_properties(self, type_data.items())
        self.encode_hierarchy()
