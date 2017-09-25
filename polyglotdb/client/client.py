import requests

from requests.exceptions import ConnectionError

from ..exceptions import ClientError
from ..structure import Hierarchy
from ..query.annotations import GraphQuery, DiscourseGraphQuery, SpeakerGraphQuery


class PGDBClient(object):
    def __init__(self, host, corpus_name=None):
        self.host = host
        if self.host.endswith('/'):
            self.host = self.host[:-1]
        self.corpus_name = corpus_name
        self.query_behavior = 'speaker'

    def create_database(self, database_name):
        end_point = '/'.join([self.host, 'api', 'database', ''])
        data = {'name': database_name}
        resp = requests.post(end_point, data=data)
        if resp.status_code != 201:
            raise ClientError('Could not create database: {}'.format(resp.text))

    def delete_database(self, database_name):
        end_point = '/'.join([self.host, 'api', 'database', database_name, ''])
        resp = requests.delete(end_point)
        if resp.status_code != 202:
            raise ClientError('Could not delete database.')

    def database_status(self, database_name=None):
        if database_name is not None:
            end_point = '/'.join([self.host, 'api', 'database', database_name, ''])
            resp = requests.get(end_point)
            return resp.json()['data']
        else:
            end_point = '/'.join([self.host, 'api', 'database', ''])
            resp = requests.get(end_point)
            return resp.json()

    def get_directory(self, database_name):

        end_point = '/'.join([self.host, 'api', 'database', database_name, 'directory', ''])
        resp = requests.get(end_point)
        return resp.json()['data']

    def get_ports(self, database_name):
        end_point = '/'.join([self.host, 'api', 'database', database_name, 'ports', ''])
        resp = requests.get(end_point)
        return resp.json()

    def corpus_status(self, corpus_name=None):
        if corpus_name is not None:
            end_point = '/'.join([self.host, 'api', 'corpus', corpus_name, ''])
            resp = requests.get(end_point)
            return resp.json()['data']
        else:
            end_point = '/'.join([self.host, 'api', 'corpus', ''])
            resp = requests.get(end_point)
            return resp.json()

    def list_databases(self):
        end_point = '/'.join([self.host, 'api', 'database', ''])
        resp = requests.get(end_point)
        return list(resp.json().keys())

    def list_corpora(self, database):
        end_point = '/'.join([self.host, 'api', 'database', database, 'corpora', ''])
        resp = requests.get(end_point)
        return list(resp.json())

    def get_source_choices(self):
        end_point = '/'.join([self.host, 'api', 'source_directories', ''])
        resp = requests.get(end_point)
        return resp.json()['data']

    def run_query(self, query, blocking=False):
        data = query.to_json()
        print('client query data', data)
        data['blocking'] = blocking
        assert 'corpus_name' in data
        end_point = '/'.join([self.host, 'api', 'corpus', data['corpus_name'], 'query', ''])
        resp = requests.post(end_point, json=data)
        if resp.status_code not in [200, 202]:
            raise ClientError('Could not run query: {}'.format(resp.text))
        print(resp.text)
        return resp.json()

    def import_corpus(self, name, source_directory, format, database_name, blocking=False):
        end_point = '/'.join([self.host, 'api', 'import_corpus', ''])
        data = {'name': name, 'source_directory': source_directory,
                'format': format, 'database_name': database_name, 'blocking': blocking}
        resp = requests.post(end_point, data=data)
        if resp.status_code != 202:
            raise ClientError('Could not import corpus: {}'.format(resp.text))

    def start_database(self, name):
        end_point = '/'.join([self.host, 'api', 'start', ''])
        data = {'name': name}
        resp = requests.post(end_point, data=data)
        if resp.status_code != 202:
            raise ClientError('Could not start database: {}'.format(resp.text))

    def stop_database(self, name):
        end_point = '/'.join([self.host, 'api', 'stop', ''])
        data = {'name': name}
        resp = requests.post(end_point, data=data)
        if resp.status_code != 202:
            raise ClientError('Could not stop database: {}'.format(resp.text))

    def get_current_corpus_status(self, corpus_name):
        end_point = '/'.join([self.host, 'api', 'corpus_status', corpus_name, ''])
        resp = requests.get(end_point)
        if resp.status_code != 200:
            raise ClientError('Could not get corpus status: {}'.format(resp.text))
        return resp.json()['data']

    def delete_corpus(self, corpus_name):
        end_point = '/'.join([self.host, 'api', 'corpus', corpus_name, ''])
        resp = requests.delete(end_point)
        if resp.status_code != 202:
            raise ClientError('Could not delete corpus: {}'.format(resp.text))

    def hierarchy(self, corpus_name):
        end_point = '/'.join([self.host, 'api', 'corpus', corpus_name, 'hierarchy', ''])
        resp = requests.get(end_point)
        if resp.status_code != 200:
            raise ClientError('Could not retrieve corpus hierarchy: {}'.format(resp.text))
        print(resp.text)
        h = Hierarchy()
        h.from_json(resp.json())
        h.corpus_name = corpus_name
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

