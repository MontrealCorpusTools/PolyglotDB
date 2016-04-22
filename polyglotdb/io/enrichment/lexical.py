
import csv
from collections import defaultdict

def parse_string(value):
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

def enrich_lexicon_from_csv(corpus_context, path, case_sensitive = False):
    with open(path, 'r', encoding = 'utf-8-sig') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect = dialect)
        header = reader.fieldnames
        word_name = header[0]
        sanitized_names = [x.replace(' ', '_') for x in header]
        data = {}
        type_data = {}
        for line in reader:
            w = line[word_name]
            if not case_sensitive:
                w = w.lower()
            data[w] = {}
            for i, f in enumerate(header):
                if f == word_name:
                    continue
                k = sanitized_names[i]
                if k not in type_data:
                    type_data[k] = defaultdict(int)
                v = parse_string(line[f])
                if v != None:
                    type_data[k][type(v)] += 1
                data[w][k] = v
    type_data = {k: max(v.keys(), key = lambda x: v[x]) for k, v in type_data.items()}
    corpus_context.enrich_lexicon(data, type_data, case_sensitive = case_sensitive)
