from polyglotdb.corpus.summarized import SummarizedContext
from polyglotdb.io.importer import (
    import_subannotation_csv,
    import_token_csv,
    import_token_csv_with_timestamp,
    subannotations_data_to_csv,
)


class AnnotatedContext(SummarizedContext):
    """
    Class that contains methods for dealing specifically with annotations on linguistic items (termed "subannotations"
    in PolyglotDB
    """

    def import_subannotations(self, data, property_data, subannotation_name, annotation_type):
        if not self.hierarchy.has_subannotation_type(subannotation_name):
            self.hierarchy.add_subannotation_type(
                self, annotation_type, subannotation_name, properties=property_data
            )
            self.encode_hierarchy()
        subannotations_data_to_csv(self, subannotation_name, data)
        import_subannotation_csv(
            self,
            subannotation_name,
            annotation_type,
            ["id", "annotated_id"] + [x[0] for x in property_data],
        )

    def enrich_tokens_with_csv(
        self,
        path,
        annotated_type,
        id_column=None,
        discourse_id_column=None,
        timestamp_column=None,
        properties=None,
    ):
        if id_column is None and discourse_id_column is None:
            raise Exception("Must provide node id column name or discourse id column name")
        if id_column:
            import_token_csv(self, path, annotated_type, id_column, properties=properties)
        else:
            import_token_csv_with_timestamp(
                self,
                path,
                annotated_type,
                timestamp_column=timestamp_column,
                discourse_column=discourse_id_column,
                properties=properties,
            )
