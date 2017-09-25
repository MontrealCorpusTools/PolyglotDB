from contextlib import contextmanager
import sys
from . import CorpusContext
from .client.client import PGDBClient, ClientError, ConnectionError


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
    except (ClientError, ConnectionError):
        pass
    try:
        client.start_database(database_name)
    except (ClientError, ConnectionError):
        pass

    try:
        db_info = client.get_ports(database_name)
        db_info['data_dir'] = client.get_directory(database_name)
        db_info['host'] = 'localhost'
        pgdb = False
    except ConnectionError:
        print('Warning: no Polyglot server available locally, using default ports.')
        db_info = {'graph_http_port': 7474, 'graph_bolt_port': 7687,
                   'acoustic_http_port': 8086, 'host': 'localhost'}
        pgdb = True
        try:
            with CorpusContext('test', **db_info) as c:
                c.execute_cypher('''MATCH (n) return n limit 1''')
        except:
            print('Could not connect to a local database. '
                  'Please check your set up and ensure that a local database is running.')
            sys.exit(1)

    try:
        yield db_info
    finally:
        if not pgdb:
            client.stop_database(database_name)
