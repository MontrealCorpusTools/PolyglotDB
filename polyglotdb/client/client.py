import requests

from requests.exceptions import ConnectionError

from ..exceptions import ClientError
from ..structure import Hierarchy
from ..query.annotations import GraphQuery, SplitQuery


class PGDBClient(object):
    """
    Simple client for interacting with ISCAN servers.
    """

    def __init__(self, host, token=None, corpus_name=None):
        self.host = host
        self.token = token
        if self.host.endswith('/'):
            self.host = self.host[:-1]
        self.corpus_name = corpus_name
        self.query_behavior = 'speaker'

    def login(self, user_name, password):
        end_point = '/'.join([self.host, 'api', 'rest-auth', 'login', ''])
        resp = requests.post(end_point, {'username': user_name, 'password': password})
        token = resp.json()['key']
        return token

    def create_database(self, database_name):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                raise ClientError('Could not create database, already exists.')

        end_point = '/'.join([self.host, 'api', 'databases', ''])
        data = {'name': database_name}
        resp = requests.post(end_point, data=data, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not create database: {}'.format(resp.text))
        return resp.json()

    def delete_database(self, database_name):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                database_id = d['id']
                break
        else:
            raise ClientError('Could not delete database, does not exist.')

        end_point = '/'.join([self.host, 'api', 'databases', str(database_id), ''])
        resp = requests.delete(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code != 204:
            raise ClientError('Could not delete database.')

    def database_status(self, database_name=None):
        if database_name is not None:
            databases = self.list_databases()
            for d in databases:
                if d['name'] == database_name:
                    database_id = d['id']
                    break
            else:
                raise ClientError('Could not find database, does not exist.')
            end_point = '/'.join([self.host, 'api', 'databases', str(database_id), ''])
            resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
            return resp.json()
        else:
            end_point = '/'.join([self.host, 'api', 'databases', ''])
            resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
            return resp.json()

    def get_directory(self, database_name):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                database_id = d['id']
                break
        else:
            raise ClientError('Could not find database, does not exist.')

        end_point = '/'.join([self.host, 'api', 'databases', str(database_id), 'data_directory', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})

        return resp.json()

    def get_ports(self, database_name):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                database_id = d['id']
                break
        else:
            raise ClientError('Could not find database, does not exist.')
        end_point = '/'.join([self.host, 'api', 'databases', str(database_id), 'ports', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        return resp.json()

    def list_databases(self):
        end_point = '/'.join([self.host, 'api', 'databases', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code != 200:
            raise ClientError('Encountered error getting list of databases: {}'.format(resp.json()))
        return resp.json()

    def list_corpora(self, database_name=None):
        if database_name is not None:
            databases = self.list_databases()
            for d in databases:
                if d['name'] == database_name:
                    database_id = d['id']
                    break
            else:
                raise ClientError('Could not find database, does not exist.')
            end_point = '/'.join([self.host, 'api', 'databases', str(database_id), 'corpora', ''])

        else:
            end_point = '/'.join([self.host, 'api', 'corpora', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        return resp.json()

    def start_database(self, database_name):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                database_id = d['id']
                break
        else:
            raise ClientError('Could not find database, does not exist.')
        end_point = '/'.join([self.host, 'api', 'databases', str(database_id), 'start', ''])
        resp = requests.post(end_point, data={}, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not start database: {}'.format(resp.text))

    def stop_database(self, database_name):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                database_id = d['id']
                break
        else:
            raise ClientError('Could not find database, does not exist.')
        end_point = '/'.join([self.host, 'api', 'databases', str(database_id), 'stop', ''])
        resp = requests.post(end_point, data={}, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not stop database: {}'.format(resp.text))
