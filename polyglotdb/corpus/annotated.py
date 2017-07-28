from .summarized import SummarizedContext

from ..io.importer import (subannotations_data_to_csv, import_subannotation_csv)

class AnnotatedContext(SummarizedContext):
    def import_subannotations(self, data, property_data, subannotation_name, annotation_type):
        subannotations_data_to_csv(self, subannotation_name, data)
        import_subannotation_csv(self, subannotation_name, annotation_type, property_data)
        self.hierarchy.add_subannotation_type(annotation_type, subannotation_name)
        for prop, t in property_data:
            t, b, e, props = d

