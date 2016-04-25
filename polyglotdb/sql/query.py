

from sqlalchemy import distinct

from .models import AnnotationType, PropertyType, Property, NumericProperty, Annotation

from .helper import get_or_create

class Lexicon(object):
    """
    The primary way of querying Word entrieis in a relational database.
    """
    def __init__(self, corpus_context):
        self.corpus_context = corpus_context
        self.cache = {}
        self.prop_type_cache = {}
        self.anno_type_cache = {}

    def __getitem__(self, key):
        if key not in self.cache:
            q =  self.corpus_context.sql_session.query(Annotation).filter(Annotation.label == key)
            word = q.first()
            self.cache[key] = word
        return self.cache[key]

    def lookup(self, key, annotation_type, case_sensitive = False):
        q =  self.corpus_context.sql_session.query(Annotation)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == annotation_type)
        if case_sensitive:
            q = q.filter(Annotation.label == key)
        else:
            q = q.filter(Annotation.label_insensitive == key)
        annotation = q.first()
        return annotation

    def add_properties(self, annotation_type, data, types, case_sensitive = False):
        for label, d in data.items():
            annotation = self.lookup(label, annotation_type, case_sensitive = case_sensitive)
            if annotation is None:
                continue
            for k, v in d.items():
                if v is None:
                    continue
                pt = self.get_or_create_property_type(k)
                if types[k] in [int, float]:
                    c = NumericProperty
                    v = float(v)
                else:
                    c = Property
                    v = str(v)
                prop, _ = get_or_create(self.corpus_context.sql_session, c,
                                    annotation = annotation, property_type = pt, value = v)

    def get_property_levels(self, property_type, annotation_type = None):
        q = self.corpus_context.sql_session.query(distinct(Property.value))
        q = q.join(PropertyType, Property.property_type_id == PropertyType.id)
        q = q.filter(PropertyType.label == property_type)
        if annotation_type is not None:
            q = q.join(Annotation, Property.annotation_id == Annotation.id)
            q = q.join(AnnotationType, Annotation.annotation_type_id == AnnotationType.id)
            q = q.filter(AnnotationType.label == annotation_type)
        return [x[0] for x in q.all()]

    def get_or_create_property_type(self, property_type):
        if property_type not in self.prop_type_cache:
            pt, _ = get_or_create(self.corpus_context.sql_session,
                                    PropertyType, label = property_type)
            self.prop_type_cache[property_type] = pt
        return self.prop_type_cache[property_type]

    def get_or_create_annotation_type(self, annotation_type):
        if annotation_type not in self.anno_type_cache:
            at, _ = get_or_create(self.corpus_context.sql_session,
                                    AnnotationType, label = annotation_type)
            self.anno_type_cache[annotation_type] = at
        return self.anno_type_cache[annotation_type]

    def get_property_type(self, property_type):
        if property_type not in self.prop_type_cache:
            q = self.corpus_context.sql_session.query(PropertyType)
            q = q.filter(PropertyType.label == property_type)
            pt = q.first()
            if pt is None:
                raise(AttributeError('Property type \'{}\' not found.'.format(property_type)))
            self.prop_type_cache[property_type] = pt
        return self.prop_type_cache[property_type]

    def get_annotation_type(self, annotation_type):
        if annotation_type not in self.anno_type_cache:
            q = self.corpus_context.sql_session.query(AnnotationType)
            q = q.filter(AnnotationType.label == annotation_type)
            at = q.first()
            if at is None:
                raise(AttributeError('Annotation type \'{}\' not found.'.format(annotation_type)))
            self.anno_type_cache[annotation_type] = at
        return self.anno_type_cache[annotation_type]


    def get_or_create_annotation(self, label, annotation_type):
        created = False
        if (label, annotation_type) not in self.cache:
            at = self.get_or_create_annotation_type(annotation_type)
            a, _ = get_or_create(self.corpus_context.sql_session,
                                    Annotation,
                                    label = label,
                                    annotation_type = at)
            self.cache[(label, annotation_type)] = a
            created = True
        return self.cache[(label, annotation_type)], created

    def list_labels(self, annotation_type):
        q =  self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == annotation_type)
        return sorted([x[0] for x in q.all()])

    def words(self):
        q =  self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == self.corpus_context.word_name)
        return sorted([x[0] for x in q.all()])

    def phones(self):
        q =  self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == self.corpus_context.phone_name)
        return sorted([x[0] for x in q.all()])
