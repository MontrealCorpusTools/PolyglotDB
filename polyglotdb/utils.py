from contextlib import contextmanager
import sys
from . import CorpusContext
from .client.client import PGDBClient, ClientError
from requests.exceptions import ConnectionError


def get_corpora_list(config):
    """
    Get a list of all corpora on using a database configuration

    Parameters
    ----------
    config : :class:`~polyglot.config.CorpusConfig`
        Config to connect with

    Returns
    -------
    list
        List of all corpora on the specified connected database
    """
    with CorpusContext(config) as c:
        statement = '''MATCH (n:Corpus) RETURN n.name as name ORDER BY name'''
        results = c.execute_cypher(statement)
    return [x['name'] for x in results]


@contextmanager
def ensure_local_database_running(database_name, port=8080, token=None, ip="localhost"):
    """
    Context manager function to ensure a locally running database exists (either ISCAN server or the pgdb
    utility is running)

    Parameters
    ----------
    database_name : str
        Name of the database
    port: int
        Port to try to connect to ISCAN server, defaults to 8080
    token : str
        Authentication token to use for ISCAN server
    ip : str
        IP address of the server(useful for Docker installations)

    Yields
    ------
    dict
        Connection parameters for a :class:`~polyglot.corpus.context.CorpusContext` object
    """

    host = 'http://{}:{}'.format(ip, port)
    client = PGDBClient(host, token=token)

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
        db_info['host'] = ip
        pgdb = False
    except ConnectionError:
        print('Warning: no ISCAN server available locally, using default ports.')
        db_info = {'graph_http_port': 7474, 'graph_bolt_port': 7687,
                   'acoustic_http_port': 8086, 'host': ip}
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
