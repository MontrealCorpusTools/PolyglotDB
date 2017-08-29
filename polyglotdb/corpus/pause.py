from .importable import ImportContext


class PauseContext(ImportContext):
    @property
    def has_pauses(self):
        return 'pause' in self.hierarchy.subset_tokens[self.word_name]

    def encode_pauses(self, pause_words, call_back=None, stop_check=None):
        """
        Set words to be pauses, as opposed to speech.

        Parameters
        ----------
        pause_words : str, list, tuple, or set
            Either a list of words that are pauses or a string containing
            a regular expression that specifies pause words
        """
        self.reset_pauses()
        word = getattr(self, self.word_name)
        q = self.query_graph(word)
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
        statement = '''MATCH (prec:{corpus}:{word_type}:speech)
        WHERE not (prec)-[:precedes]->()
        WITH prec
        MATCH p = (prec)-[:precedes_pause*]->(foll:{corpus}:{word_type}:speech)
        WITH prec, foll, p
        WHERE NONE (x in nodes(p)[1..-1] where x:speech)
        MERGE (prec)-[:precedes]->(foll)'''.format(corpus=self.cypher_safe_name,
                                                   word_type=self.word_name)

        self.execute_cypher(statement)

        statement = '''MATCH (w:{word_type}:{corpus}:speech)-[:spoken_in]->(d:Discourse:{corpus})
            with d, max(w.end) as speech_end, min(w.begin) as speech_begin
            set d.speech_begin = speech_begin,
                d.speech_end = speech_end
            return d'''.format(corpus=self.cypher_safe_name,
                               word_type=self.word_name)

        results = self.execute_cypher(statement)
        self.hierarchy.add_token_labels(self, self.word_name, ['pause'])
        self.hierarchy.add_discourse_properties(self, [('speech_begin', float), ('speech_end', float)])
        self.encode_hierarchy()

    def reset_pauses(self):
        """
        Revert all words marked as pauses to regular words marked as speech
        """
        statement = '''MATCH (n:{corpus}:{word_type}:speech)-[r:precedes]->(m:{corpus}:{word_type}:speech)
        WHERE (n)-[:precedes_pause]->()
        DELETE r'''.format(corpus=self.cypher_safe_name, word_type=self.word_name)
        self.execute_cypher(statement)

        statement = '''MATCH (n:{corpus}:{word_type})-[r:precedes_pause]->(m:{corpus}:{word_type})
        MERGE (n)-[:precedes]->(m)
        DELETE r'''.format(corpus=self.cypher_safe_name, word_type=self.word_name)
        self.execute_cypher(statement)

        statement = '''MATCH (n:pause:{corpus})
        SET n :speech
        REMOVE n:pause'''.format(corpus=self.cypher_safe_name)
        self.execute_cypher(statement)
        try:
            self.hierarchy.annotation_types.remove('pause')
            self.hierarchy.subset_tokens[self.word_name].remove('pause')
            self.encode_hierarchy()
        except KeyError:
            pass
