
from .config import session_scope

from .models import Word

class Lexicon(object):
    """
    The primary way of querying Word entrieis in a relational database.
    """
    def __init__(self):
        pass

    def __getitem__(self, key):
        with session_scope() as session:
            q = session.query(Word).filter(Word.orthography == key)
            word = q.first()
        return word

class Inventory(object):
    pass
