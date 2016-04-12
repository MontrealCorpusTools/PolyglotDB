

from .base import BaseContext

class FeaturedContext(BaseContext):
    def encode_class(self, phones, label):
        statement = '''MATCH (n:{phone_name}_type:{corpus_name}) where n.label in {{phones}}
        SET n :{label}'''.format(phone_name = self.phone_name, corpus_name = self.corpus_name,
                                label = label)
        self.execute_cypher(statement, phones = phones)
        self.hierarchy.add_type_labels(self, self.phone_name, [label])
        self.refresh_hierarchy()

    def reset_class(self, label):
        statement = '''MATCH (n:{phone_name}_type:{corpus_name})
        REMOVE n:{label}'''.format(phone_name = self.phone_name, corpus_name = self.corpus_name,
                                label = label)
        self.execute_cypher(statement)
        self.hierarchy.remove_type_labels(self, self.phone_name, [label])
        self.refresh_hierarchy()

    def encode_features(self, feature_dict):
        phone = getattr(self, self.phone_name)
        for k, v in feature_dict.items():
            q = self.query_graph(phone).filter(phone.label == k)
            q.set_type(**v)

    def reset_features(self, feature_names):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone)
        q.set_type(**{x: None for x in feature_names})
        self.hierarchy.remove_type_properties(self, self.phone_name, feature_names)
