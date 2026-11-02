import os

base_dir = os.path.dirname(os.path.abspath(__file__))

neo4j_template_path = os.path.join(base_dir, "neo4j.conf")
influxdb_template_path = os.path.join(base_dir, "influxdb.conf")


def default_config(data_directory):
    """Default settings for a pgdb install whose files live in data_directory, used
    by pgdb.py and CorpusConfig.
    """
    return {
        "Neo4j": {"http_port": 7474, "https_port": 7475, "bolt_port": 7687},
        "Neo4j_wrapper": {"initial_heap": 2048, "max_heap": 4096},
        "InfluxDB": {
            "http_port": 8086,
            "auth_enabled": "false",
            "data_directory": os.path.join(data_directory, "influxdb", "data"),
            "wal_directory": os.path.join(data_directory, "influxdb", "wal"),
            "meta_directory": os.path.join(data_directory, "influxdb", "meta"),
        },
        "Data": {"directory": data_directory},
    }
