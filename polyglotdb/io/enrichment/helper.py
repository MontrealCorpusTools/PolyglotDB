
import csv
from collections import defaultdict

def parse_string(value):
    value = value.strip()
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() in ['none', 'null', 'na']:
        return None
    try:
        v = float(value)
        return v
    except ValueError:
        return value

def parse_file(path, case_sensitive = True):
    with open(path, 'r', encoding = 'utf-8-sig') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect = dialect)
        header = reader.fieldnames
        key_name = header[0]
        sanitized_names = [x.strip().replace(' ', '_') for x in header]
        data = {}
        type_data = {}
        for line in reader:
            p = line[key_name]
            if not case_sensitive:
                p = p.lower()
            data[p] = {}
            for i, f in enumerate(header):
                if f == key_name:
                    continue
                k = sanitized_names[i]
                if k not in type_data:
                    type_data[k] = defaultdict(int)
                v = parse_string(line[f])
                if v != None:
                    type_data[k][type(v)] += 1
                data[p][k] = v
    type_data = {k: max(v.keys(), key = lambda x: v[x]) for k, v in type_data.items()}
    return data, type_data
