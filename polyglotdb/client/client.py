import requests
from ..exceptions import ClientError


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
        """
        Get an authentication token from the ISCAN server using the specified credentials

        Parameters
        ----------
        user_name : str
            User name
        password : str
            Password

        Returns
        -------
        str
            Authentication token to use in future requests
        """
        end_point = '/'.join([self.host, 'api', 'rest-auth', 'login', ''])
        resp = requests.post(end_point, {'username': user_name, 'password': password})
        token = resp.json()['key']
        self.token = token
        return token

    def create_database(self, database_name):
        """
        Create a new database with the specified name

        Parameters
        ----------
        database_name : str
            Name of the database to be created

        Returns
        -------
        dict
            Database information
        """
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
        """
        Delete a database and all associated content

        Parameters
        ----------
        database_name : str
            Name of database to be deleted
        """
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
        """
        Get the current status of a specified database, or all databases on the server.

        Parameters
        ----------
        database_name : str
            Name of database to get status of, if not specified, will get status of all databases

        Returns
        -------
        dict
            Database status JSON
        """
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
        """
        Get the directory of a local database

        Parameters
        ----------
        database_name : str
            Name of database

        Returns
        -------
        str
            Database data directory
        """
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
        """
        Get the ports of a locally running database

        Parameters
        ----------
        database_name : str
            Name of database

        Returns
        -------
        dict
            Ports of the database
        """
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
        """
        Get a list of all databases

        Returns
        -------
        list
            Database information
        """
        end_point = '/'.join([self.host, 'api', 'databases', ''])
        resp = requests.get(end_point, headers={'Authorization': 'Token {}'.format(self.token)})
        if resp.status_code != 200:
            raise ClientError('Encountered error getting list of databases: {}'.format(resp.json()))
        return resp.json()

    def list_corpora(self, database_name=None):
        """
        Get a list of all corpora

        Parameters
        ----------
        database_name : str
            Name of the database to restrict corpora list to, optional

        Returns
        -------
        list
            Corpora information
        """
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
        """
        Start a database

        Parameters
        ----------
        database_name : str
            Database to start
        """
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
        """
        Stop a database

        Parameters
        ----------
        database_name : str
            Database to stop
        """
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
