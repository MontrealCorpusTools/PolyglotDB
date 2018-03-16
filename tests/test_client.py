import pytest
import time
from polyglotdb.client.client import PGDBClient, ClientError


def test_client_create_database(graph_db, localhost, auth_token):
    print(graph_db)
    client = PGDBClient(localhost, token=auth_token)
    try:
        client.delete_database('test_database')
    except ClientError:
        pass
    with pytest.raises(ClientError):
        client.delete_database('test_database')
    client.create_database('test_database')
    with pytest.raises(ClientError):
        response = client.create_database('test_database')

    ports = client.get_ports('test_database')
    assert 'graph_http_port' in ports
    assert 'graph_bolt_port' in ports
    assert 'acoustic_http_port' in ports


def test_client_database_list(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    dbs = client.list_databases()
    assert 'test_database' in [ x['name'] for x in dbs]


def test_client_database_status(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    statuses = client.database_status()
    print(statuses)
    for s in statuses:
        if s['name'] == 'test_database':
            assert s['status'] == 'Stopped'
    status = client.database_status('test_database')
    assert status['status'] == 'Stopped'


def test_client_corpus_list(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    corpora = client.list_corpora('test_database')
    assert corpora == []


def test_client_source_directories(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    choices = client.get_source_choices()
    assert 'acoustic' in choices


def test_client_import(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    with pytest.raises(ClientError):
        client.import_corpus('test', 'acoustic', 'M', 'test_database')

    client.start_database('test_database')
    client.import_corpus('test', 'acoustic', 'M', 'test_database', blocking=True)

    client.stop_database('test_database')
    assert client.corpus_status('test')['status'] == 'Imported'
    assert 'test' in [x['name'] for x in client.list_corpora('test_database')]


def test_query_basic(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    client.start_database('test_database')
    hierarchy = client.hierarchy('test')
    q = client.generate_query(hierarchy.phone)
    q.filter(hierarchy.phone.label == 'aa')
    q.columns(hierarchy.phone.label.column_name('phone_name'))
    results = client.run_query(q, blocking=True)
    assert len(results) > 0
    assert all(x['phone_name'] == 'aa' for x in results)

    client.stop_database('test_database')


def test_client_delete_corpus(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    client.start_database('test_database')
    assert 'test' in [x['name'] for x in client.list_corpora('test_database')]
    client.delete_corpus('test')
    assert 'test' not in [x['name'] for x in client.list_corpora('test_database')]

    client.stop_database('test_database')


def test_client_delete_database(localhost, auth_token):
    client = PGDBClient(localhost, token=auth_token)
    assert 'test_database' in [x['name'] for x in client.list_databases()]
    client.delete_database('test_database')
    assert 'test_database' not in [x['name'] for x in client.list_databases()]

