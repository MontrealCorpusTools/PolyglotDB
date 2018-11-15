import csv


def make_safe(value, delimiter):
    """
    Recursively parse transcription lists into strings for saving

    Parameters
    ----------
    value : list or None
        Object to make into string

    delimiter : str
        Character to mark boundaries between list elements

    Returns
    -------
    str
        Safe string
    """
    if isinstance(value, list):
        return delimiter.join(map(lambda x: make_safe(x, delimiter), value))
    if value is None:
        return ''
    return str(value)


def save_results(results, path, header=None, mode='w'):
    """
    Writes results to path specified 

    Parameters
    ----------
    results : iterable
        the results to write
    path : str
        the path to the save file
    header : list
        Defaults to none
    mode : str
        defaults to 'w', or write. Can be 'a', append
    """
    if header is None:
        header = results.columns
    if isinstance(path, str):
        with open(path, mode, encoding='utf8', newline='') as f:
            writer = csv.DictWriter(f, header)
            if mode != 'a':
                writer.writeheader()
            for line in results:
                try:
                    line = {k: make_safe(line[k], '/') for k in header}
                except KeyError:
                    continue
                writer.writerow(line)
    else:
        if mode != 'a':
            path.writerow(header)
        for line in results:
            try:
                line = [make_safe(line[k], '/') for k in header]
            except KeyError:
                continue
            path.writerow(line)

