

from .models import Word, InventoryItem, AnnotationType, WordPropertyType

from .helper import get_or_create

class Lexicon(object):
    """
    The primary way of querying Word entrieis in a relational database.
    """
    def __init__(self, corpus_context):
        self.corpus_context = corpus_context
        self.cache = {}
        self.prop_type_cache = {}

    def __getitem__(self, key):
        q =  self.corpus_context.sql_session.query(Word).filter(Word.orthography == key)
        word = q.first()
        return word

    def get_property_type(self, property_type):
        if property_type not in self.prop_type_cache:
            q = self.corpus_context.sql_session.query(WordPropertyType)
            q = q.filter(WordPropertyType.label == property_type)
            pt = q.first()
            if pt is None:
                raise(Exception('Annotation type \'{}\' not found.'.format(property_type)))
            self.prop_type_cache[property_type] = pt
        return self.prop_type_cache[property_type]

    def get_or_create_word(self, orthography, transcription):
        created = False
        if (orthography, transcription) not in self.cache:
            w, _ = get_or_create(self.corpus_context.sql_session,
                                    Word, defaults = {'frequency':0},
                                    orthography = orthography,
                                    transcription = transcription)
            self.cache[(orthography, transcription)] = w
            created = True
        return self.cache[(orthography, transcription)], created

class Inventory(object):
    def __init__(self, corpus_context):
        self.corpus_context = corpus_context
        self.cache = {}
        self.type_cache = {}

    def __getitem__(self, key):
        q =  self.corpus_context.sql_session.query(InventoryItem).filter(InventoryItem.label == key)
        item = q.first()
        return item

    def get_annotation_type(self, annotation_type):
        if annotation_type not in self.type_cache:
            q = self.corpus_context.sql_session.query(AnnotationType)
            q = q.filter(AnnotationType.label == annotation_type)
            at = q.first()
            if at is None:
                raise(Exception('Annotation type \'{}\' not found.'.format(annotation_type)))
            self.type_cache[annotation_type] = at
        return self.type_cache[annotation_type]

    def get_or_create_item(self, label, annotation_type):
        if isinstance(annotation_type, str):
            annotation_type = self.get_annotation_type(annotation_type)
        created = False
        if (label, annotation_type) not in self.cache:
            p, _ = get_or_create(self.corpus_context.sql_session,
                                InventoryItem, label = label,
                                annotation_type = annotation_type)
            self.cache[(label, annotation_type)] = p
            created = True
        return self.cache[(label, annotation_type)], created
