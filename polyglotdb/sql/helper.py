from sqlalchemy.sql.expression import ClauseElement

def get_or_create(session, model, defaults=None, **kwargs):
    """
    either get or create a session
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True
