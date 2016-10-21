from sqlalchemy.sql.expression import ClauseElement

def get_or_create(session, model, defaults=None, **kwargs):
    """
    either get or create a row in the sql table specified by model

    Parameters
    ----------
    Session : corpus_context.sqlsession 
        the current sql session
    model : a  ~declarative_base model
        the table to add data to
    defaults:

    **kwargs: 
        the data to add
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
