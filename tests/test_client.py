import pytest
import time
from polyglotdb.client.client import PGDBClient, ClientError


def test_client_create_database(localhost):
    client = PGDBClient(localhost)
    try:
        client.delete_database('test_database')
    except ClientError:
        pass
    with pytest.raises(ClientError):
        client.delete_database('test_database')
    client.create_database('test_database')
    with pytest.raises(ClientError):
        response = client.create_database('test_database')


def test_client_database_list(localhost):
    client = PGDBClient(localhost)
    dbs = client.list_databases()
    assert 'test_database' in dbs


def test_client_database_status(localhost):
    client = PGDBClient(localhost)
    statuses = client.database_status()
    assert statuses['test_database'] == 'Stopped'
    status = client.database_status('test_database')
    assert status == 'Stopped'


def test_client_corpus_list(localhost):
    client = PGDBClient(localhost)
    corpora = client.list_corpora()
    assert corpora == []


def test_client_source_directories(localhost):
    client = PGDBClient(localhost)
    choices = client.get_source_choices()
    assert choices == ['cont']


def test_client_import(localhost):
    client = PGDBClient(localhost)
    with pytest.raises(ClientError):
        client.import_corpus('test', 'cont', 'M', 'test_database')

    client.start_database('test_database')
    time.sleep(10)
    client.import_corpus('test', 'cont', 'M', 'test_database')
    while client.get_current_corpus_status('test') == 'busy':
        time.sleep(10)
    client.stop_database('test_database')
    assert client.corpus_status('test') == 'Imported'
    assert 'test' in client.list_corpora()
    time.sleep(30)


def test_query_basic(localhost):
    client = PGDBClient(localhost)
    client.start_database('test_database')
    time.sleep(10)
    hierarchy = client.hierarchy('test')
    q = client.generate_query(hierarchy.phone)
    q.filter(hierarchy.phone.label == 'B')
    q.columns(hierarchy.phone.label.column_name('phone_name'))
    results = client.run_query(q)
    assert all(x['phone_name'] == 'B' for x in results)

    client.stop_database('test_database')
    time.sleep(10)


def test_client_delete_corpus(localhost):
    client = PGDBClient(localhost)
    client.start_database('test_database')
    time.sleep(10)
    assert 'test' in client.list_corpora()
    client.delete_corpus('test')
    assert 'test' not in client.list_corpora()

    client.stop_database('test_database')
    time.sleep(10)
