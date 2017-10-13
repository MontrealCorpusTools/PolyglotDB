import os

base_dir = os.path.dirname(os.path.abspath(__file__))

neo4j_template_path = os.path.join(base_dir, 'neo4j.conf')
influxdb_template_path = os.path.join(base_dir, 'influxdb.conf')