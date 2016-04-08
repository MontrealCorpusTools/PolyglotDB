

from .base import BaseContext

class FeaturedContext(BaseContext):
    def encode_class(self, phones, label):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone).filter(phone.label.in_(phones))
        q.set_type(label)

    def reset_class(self, label):
        phone = getattr(self, self.phone_name)
        q = self.query_graph(phone).filter(phone.type_subset == label)
        q.remove_type_labels(label)

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
