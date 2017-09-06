
from contextlib import contextmanager
from . import CorpusContext
from .client.client import PGDBClient, ClientError

def get_corpora_list(config):
    with CorpusContext(config) as c:
        statement = '''MATCH (n:Corpus) RETURN n.name as name ORDER BY name'''
        results = c.execute_cypher(statement)
    return [x['name'] for x in results]


@contextmanager
def ensure_local_database_running(database_name):
    client = PGDBClient('http://localhost:8000')

    try:
        response = client.create_database(database_name)
    except ClientError:
        pass
    try:
        client.start_database(database_name)
    except ClientError:
        pass

    db_info = client.get_ports(database_name)
    db_info['data_dir'] = client.get_directory(database_name)
    db_info['host'] = 'localhost'

    try:
        yield db_info
    finally:
        client.stop_database(database_name)