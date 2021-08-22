from .importable import ImportContext


class PauseContext(ImportContext):
    """
    Class that contains methods for dealing specifically with non-speech elements
    """
    @property
    def has_pauses(self):
        """
        Check whether corpus has encoded pauses

        Returns
        -------
        bool
            True if pause is in the subsets available for words
        """
        return 'pause' in self.hierarchy.subset_tokens[self.word_name]

    def encode_pauses(self, pause_words, call_back=None, stop_check=None):
        """
        Set words to be pauses, as opposed to speech.

        Parameters
        ----------
        pause_words : str, list, tuple, or set
            Either a list of words that are pauses or a string containing
            a regular expression that specifies pause words
        call_back : callable
            Function to monitor progress
        stop_check : callable
            Function to check whether process should be terminated early
        """
        self.reset_pauses()
        word = getattr(self, self.word_name)
        for s in self.speakers:
            discourses = self.get_discourses_of_speaker(s)
            for d in discourses:
                q = self.query_graph(word)
                q = q.filter(word.speaker.name == s)
                q = q.filter(word.discourse.name == d)
                if call_back is not None:
                    q.call_back = call_back
                if stop_check is not None:
                    q.stop_check = stop_check
                if isinstance(pause_words, (list, tuple, set)):
                    q = q.filter(word.label.in_(pause_words))
                elif isinstance(pause_words, str):
                    q = q.filter(word.label.regex(pause_words))
                else:
                    raise (NotImplementedError)
                q.set_pause()

        if call_back is not None:
            call_back('Finishing up...')
        for s in self.speakers:
            discourses = self.get_discourses_of_speaker(s)
            for d in discourses:
                statement = '''MATCH (prec:{corpus}:{word_type}:speech)-[:spoken_by]->(s:Speaker:{corpus}),
                (prec)-[:spoken_in]->(d:Discourse:{corpus})
                WHERE not (prec)-[:precedes]->()
                AND s.name = $speaker
                AND d.name = $discourse
                WITH prec
                MATCH p = (prec)-[:precedes_pause*]->(foll:{corpus}:{word_type}:speech)
                WITH prec, foll, p
                WHERE NONE (x in nodes(p)[1..-1] where x:speech)
                MERGE (prec)-[:precedes]->(foll)'''.format(corpus=self.cypher_safe_name,
                                                           word_type=self.word_name)

                self.execute_cypher(statement, speaker=s, discourse=d)

                statement = '''MATCH (s:Speaker:{corpus})<-[:spoken_by]-(w:{word_type}:{corpus}:speech)-[:spoken_in]->(d:Discourse:{corpus})
                WHERE s.name = $speaker
                AND d.name = $discourse
                    with d, max(w.end) as speech_end, min(w.begin) as speech_begin
                    set d.speech_begin = speech_begin,
                        d.speech_end = speech_end
                    return d'''.format(corpus=self.cypher_safe_name,
                                       word_type=self.word_name)

                results = self.execute_cypher(statement, speaker=s, discourse=d)
        self.hierarchy.add_token_subsets(self, self.word_name, ['pause'])
        self.hierarchy.add_discourse_properties(self, [('speech_begin', float), ('speech_end', float)])
        self.encode_hierarchy()

    def reset_pauses(self):
        """
        Revert all words marked as pauses to regular words marked as speech
        """
        for s in self.speakers:
            discourses = self.get_discourses_of_speaker(s)
            for d in discourses:
                statement = '''MATCH (n:{corpus}:{word_type}:speech)-[r:precedes]->(m:{corpus}:{word_type}:speech),
                (m)-[:spoken_by]->(s:Speaker:{corpus}),
                (m)-[:spoken_in]->(d:Discourse:{corpus})
                WHERE (n)-[:precedes_pause]->()
                AND s.name = $speaker
                AND d.name = $discourse
                DELETE r'''.format(corpus=self.cypher_safe_name, word_type=self.word_name)
                self.execute_cypher(statement, speaker=s, discourse=d)

                statement = '''MATCH (n:{corpus}:{word_type})-[r:precedes_pause]->(m:{corpus}:{word_type}),
                (m)-[:spoken_by]->(s:Speaker:{corpus}),
                (m)-[:spoken_in]->(d:Discourse:{corpus})
                WHERE s.name = $speaker
                AND d.name = $discourse
                MERGE (n)-[:precedes]->(m)
                DELETE r'''.format(corpus=self.cypher_safe_name, word_type=self.word_name)
                self.execute_cypher(statement, speaker=s, discourse=d)

                statement = '''MATCH (n:pause:{corpus})-[:spoken_by]->(s:Speaker:{corpus}),
                (n)-[:spoken_in]->(d:Discourse:{corpus})
                WHERE s.name = $speaker
                AND d.name = $discourse
                SET n :speech
                REMOVE n:pause'''.format(corpus=self.cypher_safe_name)
                self.execute_cypher(statement, speaker=s, discourse=d)
        try:
            self.hierarchy.subset_tokens[self.word_name].remove('pause')
            self.encode_hierarchy()
        except (KeyError, ValueError):
            pass
