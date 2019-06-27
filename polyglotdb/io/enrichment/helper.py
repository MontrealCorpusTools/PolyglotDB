import csv
from collections import defaultdict
from ...exceptions import ParseError


def sanitize_name(string):
    """
    Sanitize name by removing trailing whitespace and replacing any string-internal whitespace with underscores

    Parameters
    ----------
    string : str
        Name to be sanitized

    Returns
    -------
    str
        Sanitized string
    """
    if "." in string:
        raise ParseError("Column name, \"{}\" contains a period which is not permitted in CSVs used by PolyglotDB".format(string))
    return string.strip().replace(' ', '_').lower()


def parse_string(value):
    """
    parses string for python keywords or numeric value

    Parameters
    ----------
    value : str or float
        the value to be parsed (true, false, none, null, na, or float)

    Returns
    -------
    boolean, None, float, original value
    """
    if value is None:
        return None
    value = value.strip()
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() in ['none', 'null', 'na']:
        return None
    try:
        if '.' in value:
            v = float(value)
        else:
            v = int(value)
        return v
    except ValueError:
        return value


def parse_file(path, labels=None, case_sensitive=True):
    """
    Parses a csv file into data and type_data

    Parameters
    ----------
    path : str
        the path to the file
    labels : list, optional
        List of labels to limit file parsing to
    case_sensitive : boolean
        Defaults to true

    Returns
    -------
    tuple
        data and type_data for a csv file
    """
    with open(path, 'r', encoding='utf-8-sig') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read())
        if dialect.delimiter == '-':
            dialect.delimiter = ','
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        header = reader.fieldnames
        key_name = header[0]
        sanitized_names = [sanitize_name(x) for x in header]
        data = {}
        type_data = {}
        if not labels:
            for line in reader:
                p = line[key_name]

                for i, f in enumerate(header):
                    if f == key_name:
                        continue
                    k = sanitized_names[i]
                    if k not in type_data:
                        type_data[k] = defaultdict(int)
                    v = parse_string(line[f])
                    if v is not None:
                        type_data[k][type(v)] += 1
                if not case_sensitive:
                    p = p.lower()
                data[p] = {}
                for i, f in enumerate(header):
                    if f == key_name:
                        continue
                    k = sanitized_names[i]
                    v = parse_string(line[f])
                    data[p][k] = v
        else:
            for line in reader:
                p = line[key_name]

                for i, f in enumerate(header):
                    if f == key_name:
                        continue
                    k = sanitized_names[i]
                    if k not in type_data:
                        type_data[k] = defaultdict(int)
                    v = parse_string(line[f])
                    if v is not None:
                        type_data[k][type(v)] += 1
                if not case_sensitive:
                    p = p.lower()
                if labels is not None and p not in labels:
                    continue
                data[p] = {}
                for i, f in enumerate(header):
                    if f == key_name:
                        continue
                    k = sanitized_names[i]
                    v = parse_string(line[f])
                    data[p][k] = v
        type_data = {k: max(v.keys(), key=lambda x: v[x]) for k, v in type_data.items()}
        return data, type_data
