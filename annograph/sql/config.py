
from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker

Session = sessionmaker(expire_on_commit=False)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.expunge_all()
        session.close()
