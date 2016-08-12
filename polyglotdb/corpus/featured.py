
import re
from ..io.importer import feature_data_to_csvs, import_feature_csvs

class FeaturedContext(object):
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
        statement = '''MATCH (n:{phone_name}_type:{corpus_name}) where n.label in {{phones}}
        SET n :{label}'''.format(phone_name = self.phone_name, corpus_name = self.cypher_safe_name,
                                label = label)
        
        self.execute_cypher(statement, phones = phones)
        self.hierarchy.add_type_labels(self, self.phone_name, [label])
        self.refresh_hierarchy()

    def reset_class(self, label):
        """
        resets the class
        """
        statement = '''MATCH (n:{phone_name}_type:{corpus_name}:{label})
        REMOVE n:{label}'''.format(phone_name = self.phone_name, corpus_name = self.cypher_safe_name,
                                label = label)
        self.execute_cypher(statement)
        self.hierarchy.remove_type_labels(self, self.phone_name, [label])
        self.refresh_hierarchy()

    def encode_features(self, feature_dict):
        """
        gets the phone if it exists, queries for each phone and sets type to kwargs (?)

        Parameters
        ----------
        feature_dict : dict
            features to encode
        """
        phone = getattr(self, self.phone_name)
        for k, v in feature_dict.items():
            q = self.query_graph(phone).filter(phone.label == k)
            q.set_type(**v)

    def reset_features(self, feature_names):
        """
        resets features 

        Parameters
        ----------
        feature_names : list
            list of names of features to remove
        """
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone)
        q.set_type(**{x: None for x in feature_names})
        self.hierarchy.remove_type_properties(self, self.phone_name, feature_names)

    def enrich_features(self, feature_data, type_data = None):
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
            type_data = {k: type(v) for k,v in next(iter(feature_data.values())).items()}
        labels = set(self.lexicon.phones())
        feature_data = {k: v for k,v in feature_data.items() if k in labels}
        self.lexicon.add_properties(self.phone_name, feature_data, type_data)
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
        phone = getattr(self,self.phone_name)
        if pattern == '':
            pattern = '[0-2]'
        q = self.query_graph(phone)
        results = q.all()
        oldphones = []
        length = 0
        newphones=[]
        toAdd = {}
        for c in results.cursors:
            for item in c:
                phone = item[0].properties['label']
                if re.search(pattern, phone) is not None:
                    newphone = re.sub(pattern, "", phone)
                    length = len(phone)-len(newphone)
                    oldphones.append(phone)
                    newphones.append(newphone)
                    toAdd.update({'label':newphone})
        statement = '''MATCH (n:{phone_name}{type}:{corpus_name}) WHERE n.label in {{oldphones}} 
        SET n.oldlabel = n.label 
        SET n.label=substring(n.label,0,length(n.label)-{length})'''
        norm_statement = statement.format(phone_name=self.phone_name,type='', 
            corpus_name = self.cypher_safe_name, length = length)
        type_statement = statement.format(phone_name=self.phone_name,type='_type', 
            corpus_name = self.cypher_safe_name, length = length)
        self.execute_cypher(norm_statement, oldphones = oldphones)
        self.execute_cypher(type_statement, oldphones=oldphones)
        self.encode_syllabic_segments(newphones)
        self.encode_syllables('maxonset')
        self.refresh_hierarchy()
    def reset_to_old_label(self):
        """
        Reset phones back to their old labels which include stress and tone
        """
        phones = []
        phone = getattr(self,self.phone_name)
        getphone = '''MATCH (n:{phone_name}_type:{corpus_name})
        WHERE n.oldlabel IS NOT NULL
        RETURN n.oldlabel'''.format(phone_name=self.phone_name, 
            corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(getphone)
        for item in results:
            phones.append(item['n.oldlabel'])
        
        statement = '''MATCH (n:{phone_name}{type}:{corpus_name}) 
        WHERE n.oldlabel IS NOT NULL SET n.label = n.oldlabel'''
        norm_statement = statement.format(phone_name=self.phone_name,type="", corpus_name=self.cypher_safe_name)
        type_statement = statement.format(phone_name=self.phone_name,type="_type", corpus_name=self.cypher_safe_name)
        self.execute_cypher(norm_statement)
        self.execute_cypher(type_statement)
        self.encode_syllabic_segments(phones)
        self.encode_syllables('maxonset')
        self.refresh_hierarchy




