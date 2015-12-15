
def truncate_string(string, length = 10):
    return (string[:length] + '...') if len(string) > length + 3 else string

