

from .models import Word, InventoryItem

class Lexicon(object):
    """
    The primary way of querying Word entrieis in a relational database.
    """
    def __init__(self, corpus_context):
        self.corpus_context = corpus_context

    def __getitem__(self, key):
        q =  self.corpus_context.sql_session.query(Word).filter(Word.orthography == key)
        word = q.first()
        return word

class Inventory(object):
    def __init__(self, corpus_context):
        self.corpus_context = corpus_context

    def __getitem__(self, key):
        q =  self.corpus_context.sql_session.query(InventoryItem).filter(InventoryItem.label == key)
        item = q.first()
        return item
