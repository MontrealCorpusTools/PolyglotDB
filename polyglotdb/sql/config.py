from sqlalchemy.orm import sessionmaker

Session = sessionmaker(expire_on_commit=False)
