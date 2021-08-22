import re
from ..io.importer import feature_data_to_csvs, import_feature_csvs
from .lexical import LexicalContext
from ..io.enrichment.features import enrich_features_from_csv, parse_file


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
        self.encode_type_subset('phone', phones, label)

    def reset_class(self, label):
        """
        Reset and remove a subset

        Parameters
        ----------
        label : str
            Subset name to remove
        """
        self.reset_type_subset('phone', label)

    def encode_features(self, feature_dict):
        """
        gets the phone if it exists, queries for each phone and sets type to kwargs (?)

        Parameters
        ----------
        feature_dict : dict
            features to encode
        """
        phone = getattr(self, 'lexicon_' + self.phone_name)
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
        phone = getattr(self, 'lexicon_' + self.phone_name)
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

    def remove_pattern(self, pattern='[0-2]'):
        """
        removes a stress or tone pattern from all phones

        Parameters
        ----------
        pattern : str
            the regular expression for the pattern to remove
            Defaults to '[0-2]'

        """
        phone = getattr(self, self.phone_name)
        if pattern == '':
            pattern = '[0-2]'
        q = self.query_graph(phone)
        results = q.all()
        oldphones = []
        length = 0
        newphones = []
        toAdd = {}
        for item in results:
            phone = item['label']
            if re.search(pattern, phone) is not None:
                newphone = re.sub(pattern, "", phone)
                length = len(phone) - len(newphone)
                oldphones.append(phone)
                newphones.append(newphone)
                toAdd.update({'label': newphone})
        statement = '''MATCH (n:{phone_name}{type}:{corpus_name}) WHERE n.label in $oldphones 
        SET n.oldlabel = n.label 
        SET n.label=substring(n.label,0,size(n.label)-{length})'''
        norm_statement = statement.format(phone_name=self.phone_name, type='',
                                          corpus_name=self.cypher_safe_name, length=length)
        type_statement = statement.format(phone_name=self.phone_name, type='_type',
                                          corpus_name=self.cypher_safe_name, length=length)
        self.execute_cypher(norm_statement, oldphones=oldphones)
        self.execute_cypher(type_statement, oldphones=oldphones)
        self.encode_syllabic_segments(newphones)
        self.encode_syllables('maxonset')

    def reset_to_old_label(self):
        """
        Reset phones back to their old labels which include stress and tone
        """
        phones = []
        phone = getattr(self, self.phone_name)
        getphone = '''MATCH (n:{phone_name}_type:{corpus_name})
        WHERE n.oldlabel IS NOT NULL
        RETURN n.oldlabel'''.format(phone_name=self.phone_name,
                                    corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(getphone)
        for item in results:
            phones.append(item['n.oldlabel'])

        statement = '''MATCH (n:{phone_name}{type}:{corpus_name}) 
        WHERE n.oldlabel IS NOT NULL SET n.label = n.oldlabel'''
        norm_statement = statement.format(phone_name=self.phone_name, type="", corpus_name=self.cypher_safe_name)
        type_statement = statement.format(phone_name=self.phone_name, type="_type", corpus_name=self.cypher_safe_name)
        self.execute_cypher(norm_statement)
        self.execute_cypher(type_statement)
        self.encode_syllabic_segments(phones)
        self.encode_syllables('maxonset')
