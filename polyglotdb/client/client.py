import requests

from ..exceptions import ClientError


class PGDBClient(object):
    def __init__(self, host, corpus_name=None):
        self.host = host
        if self.host.endswith('/'):
            self.host = self.host[:-1]
        self.corpus_name = corpus_name

    def create_database(self, database_name):
        end_point = '/'.join([self.host, 'api', 'database', ''])
        data = {'name': database_name}
        resp = requests.post(end_point, data=data)
        if resp.status_code != 201:
            raise ClientError('Could not create database: {}'.format(resp.text))

    def delete_database(self, database_name):
        end_point = '/'.join([self.host, 'api', 'database', database_name, ''])
        resp = requests.delete(end_point)
        if resp.status_code != 201:
            raise ClientError('Could not delete database.')

    def database_status(self, database_name=None):
        if database_name is not None:
            end_point = '/'.join([self.host, 'api', 'database', database_name, ''])
            resp = requests.get(end_point)
            print(resp.text)
            return resp.json()['data']
        else:
            end_point = '/'.join([self.host, 'api', 'database', ''])
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

    def list_corpora(self):
        end_point = '/'.join([self.host, 'api', 'corpus', ''])
        resp = requests.get(end_point)
        return list(resp.json().keys())

    def get_source_choices(self):
        end_point = '/'.join([self.host, 'api', 'source_directories', ''])
        resp = requests.get(end_point)
        return resp.json()['data']

    def run_query(self, query):
        raise (NotImplementedError)

    def import_corpus(self, name, source_directory, format, database_name):
        end_point = '/'.join([self.host, 'api', 'import_corpus', ''])
        data = {'name': name, 'source_directory': source_directory,
                'format': format, 'database_name': database_name}
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

    def get_current_corpus_status(self, name):
        end_point = '/'.join([self.host, 'api', 'corpus_status', name, ''])
        resp = requests.get(end_point)
        if resp.status_code != 200:
            raise ClientError('Could not get corpus status: {}'.format(resp.text))
        return resp.json()['data']

    def delete_corpus(self, name):
        end_point = '/'.join([self.host, 'api', 'corpus', name, ''])
        resp = requests.delete(end_point)
        if resp.status_code != 202:
            raise ClientError('Could not delete corpus: {}'.format(resp.text))

    def hierarchy(self, corpus_name):
        raise (NotImplementedError)
