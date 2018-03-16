import requests

from requests.exceptions import ConnectionError

from ..exceptions import ClientError
from ..structure import Hierarchy
from ..query.annotations import GraphQuery, DiscourseGraphQuery, SpeakerGraphQuery


class PGDBClient(object):
    def __init__(self, host, token=None, corpus_name=None):
        self.host = host
        self.token = token
        if self.host.endswith('/'):
            self.host = self.host[:-1]
        self.corpus_name = corpus_name
        self.query_behavior = 'speaker'

    def login(self, user_name, password):
        end_point = '/'.join([self.host, 'api', 'api-token-auth', ''])
        resp = requests.post(end_point, {'username':user_name, 'password':password})
        token = resp.json()['token']
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
        print(resp.json())
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

    def corpus_status(self, corpus_name=None):
        if corpus_name is not None:
            corpora = self.list_corpora()
            for d in corpora:
                if d['name'] == corpus_name:
                    corpus_id = d['id']
                    break
            else:
                raise ClientError('Could not find corpus, does not exist.')
            end_point = '/'.join([self.host, 'api', 'corpora', str(corpus_id), ''])
            resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
            return resp.json()
        else:
            end_point = '/'.join([self.host, 'api', 'corpora', ''])
            resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
            return resp.json()

    def list_databases(self):
        end_point = '/'.join([self.host, 'api', 'databases', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
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

    def get_source_choices(self):
        end_point = '/'.join([self.host, 'api', 'source_directories', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        return resp.json()

    def run_query(self, query, blocking=False):
        data = query.to_json()
        corpus_name = data['corpus_name']
        corpora = self.list_corpora()
        for d in corpora:
            if d['name'] == corpus_name:
                corpus_id = d['id']
                break
        else:
            raise ClientError('Could not find corpus, does not exist.')
        print('client query data', data)
        data['blocking'] = blocking
        assert 'corpus_name' in data
        end_point = '/'.join([self.host, 'api', 'corpora', str(corpus_id), 'query', ''])
        resp = requests.post(end_point, json=data, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not run query: {}'.format(resp.text))
        print(resp.text)
        return resp.json()

    def import_corpus(self, name, source_directory, format, database_name, blocking=False):
        databases = self.list_databases()
        for d in databases:
            if d['name'] == database_name:
                database_id = d['id']
                break
        else:
            raise ClientError('Could not find database, does not exist.')
        corpora = self.list_corpora()
        for d in corpora:
            if d['name'] == name:
                corpus_id = d['id']
                break
        else:
            end_point = '/'.join([self.host, 'api', 'corpora', ''])
            data = {'name': name, 'source_directory': source_directory,
                    'format': format, 'database': database_id}
            resp = requests.post(end_point,data=data, headers={'Authorization': 'Token {}'.format(self.token)})
            print(resp.json())
            corpus_id = resp.json()['id']

        end_point = '/'.join([self.host, 'api', 'corpora', str(corpus_id), 'import_corpus', ''])
        data = {'blocking': blocking}
        resp = requests.post(end_point, data=data, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not import corpus: {}'.format(resp.text))

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
        print(resp)
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
        end_point = '/'.join([self.host, 'api', 'databases',  str(database_id), 'stop', ''])
        resp = requests.post(end_point, data={}, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not stop database: {}'.format(resp.text))

    def get_current_corpus_status(self, corpus_name):
        end_point = '/'.join([self.host, 'api', 'corpus_status', corpus_name, ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not get corpus status: {}'.format(resp.text))
        return resp.json()

    def delete_corpus(self, corpus_name):
        corpora = self.list_corpora()
        for d in corpora:
            if d['name'] == corpus_name:
                corpus_id = d['id']
                break
        else:
            raise ClientError('Could not find corpus, does not exist.')
        end_point = '/'.join([self.host, 'api', 'corpora', str(corpus_id), ''])
        resp = requests.delete(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code != 204:
            raise ClientError('Could not delete corpus: {}'.format(resp.text))

    def hierarchy(self, corpus_name):
        corpora = self.list_corpora()
        for d in corpora:
            if d['name'] == corpus_name:
                corpus_id = d['id']
                break
        else:
            raise ClientError('Could not find corpus, does not exist.')
        end_point = '/'.join([self.host, 'api', 'corpora', str(corpus_id), 'hierarchy', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code not in [200, 201, 202]:
            raise ClientError('Could not retrieve corpus hierarchy: {}'.format(resp.text))
        h = Hierarchy()
        h.from_json(resp.json())
        return h

    def generate_query(self, annotation_type):
        """
        Return a Query object for the specified annotation type.

        Parameters
        ----------
        annotation_type : AnnotationAttribute
            The type of annotation to look for in the corpus

        Returns
        -------
        GraphQuery
            Query object

        """
        if self.query_behavior == 'speaker':
            cls = SpeakerGraphQuery
        elif self.query_behavior == 'discourse':
            cls = DiscourseGraphQuery
        else:
            cls = GraphQuery
        return cls(annotation_type.hierarchy, annotation_type)

