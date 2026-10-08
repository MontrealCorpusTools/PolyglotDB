from polyglotdb.corpus.lexical import LexicalContext
from polyglotdb.io.enrichment.features import enrich_features_from_csv, parse_file
from polyglotdb.io.importer import feature_data_to_csvs, import_feature_csvs


class PhonologicalContext(LexicalContext):
    """
    Class that contains methods for dealing specifically with phones
    """

    def enrich_inventory_from_csv(self, path):
        """
        Enriches corpus from a csv file

        Parameters
        ----------
        path : str
            the path to the csv file
        """

        enrich_features_from_csv(self, path)

    def reset_inventory_csv(self, path):
        """
        Remove properties that were encoded via a CSV file

        Parameters
        ----------
        path : str
            CSV file to get property names from
        """
        data, type_data = parse_file(path, labels=[])

        property_names = [x for x in type_data.keys()]
        self.reset_features(property_names)

    def encode_class(self, phones, label):
        """
        encodes phone classes

        Parameters
        ----------
        phones : list
            a list of phones
        label : str
            the label for the class
        """
        self.encode_type_subset("phone", phones, label)

    def reset_class(self, label):
        """
        Reset and remove a subset

        Parameters
        ----------
        label : str
            Subset name to remove
        """
        self.reset_type_subset("phone", label)

    def encode_features(self, feature_dict):
        """
        gets the phone if it exists, queries for each phone and sets type to kwargs (?)

        Parameters
        ----------
        feature_dict : dict
            features to encode
        """
        phone = getattr(self, "lexicon_" + self.phone_name)
        for k, v in feature_dict.items():
            q = self.query_lexicon(phone).filter(phone.label == k)
            q.set_properties(**v)
        self.encode_hierarchy()

    def reset_features(self, feature_names):
        """
        resets features

        Parameters
        ----------
        feature_names : list
            list of names of features to remove
        """
        phone = getattr(self, "lexicon_" + self.phone_name)
        q = self.query_lexicon(phone)
        q.set_properties(**{x: None for x in feature_names})
        self.hierarchy.remove_type_properties(self, self.phone_name, feature_names)
        self.encode_hierarchy()

    def enrich_features(self, feature_data, type_data=None):
        """
        Sets the data type and feature data, initializes importers for feature data, adds features to hierarchy for a phone

        Parameters
        ----------
        feature_data : dict
            the enrichment data
        type_data : dict
            By default None
        """

        if type_data is None:
            type_data = {k: type(v) for k, v in next(iter(feature_data.values())).items()}
        labels = set(self.phones)
        feature_data = {k: v for k, v in feature_data.items() if k in labels}
        feature_data_to_csvs(self, feature_data)
        import_feature_csvs(self, type_data)
        self.hierarchy.add_type_properties(self, self.phone_name, type_data.items())
        self.encode_hierarchy()

    def remove_pattern(self, annotation_type: str = None, pattern: str = "[0-2]"):
        """
        Removes a stress or tone pattern from all phones

        Parameters
        ----------
        annotation_type: str
            Type of annotation to remove pattern, defaults to phones if not specified
        pattern : str
            the regular expression for the pattern to remove
            Defaults to '[0-2]'

        """
        if not annotation_type:
            annotation_type = self.phone_name
        if not pattern:
            pattern = "[0-2]"
        match_pattern = pattern
        if not match_pattern.startswith("^"):
            match_pattern = ".*" + match_pattern
        if not match_pattern.endswith("$"):
            match_pattern += ".*"
        statement = """CYPHER 25
        MATCH (n:{annotation_type}{type}:{corpus_name}) WHERE n.label =~ $match_regex
        SET n.old_label = n.label
        SET n.label=string.regexReplace(n.label, $regex, "")"""
        norm_statement = statement.format(
            annotation_type=annotation_type,
            type="",
            corpus_name=self.cypher_safe_name,
        )
        type_statement = statement.format(
            annotation_type=annotation_type,
            type="_type",
            corpus_name=self.cypher_safe_name,
        )
        self.execute_cypher(norm_statement, match_regex=match_pattern, regex=pattern)
        self.execute_cypher(type_statement, match_regex=match_pattern, regex=pattern)

    def reset_to_old_label(self, annotation_type: str = None):
        """
        Reset phones back to their old labels which include stress and tone

        Parameters
        ----------
        annotation_type: str
            Type of annotation to reset, defaults to phones if not specified
        """
        if not annotation_type:
            annotation_type = self.phone_name

        statement = f"""MATCH (n:{annotation_type}{{type}}:{self.cypher_safe_name})
        WHERE n.old_label IS NOT NULL SET n.label = n.old_label"""
        token_statement = statement.format(type="")
        type_statement = statement.format(type="_type")
        self.execute_cypher(token_statement)
        self.execute_cypher(type_statement)
