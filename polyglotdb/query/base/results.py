class BaseRecord(object):
    def __init__(self, result):
        self.columns = list(result.keys())
        self.values = list(result.values())

    def __getitem__(self, key):
        if key in self.columns:
            return self.values[self.columns.index(key)]
        raise KeyError('{} not in columns {}'.format(key, self.columns))

    def __str__(self):
        return ', '.join('{}: {}'.format(k, v) for k, v in zip(self.columns, self.values))

class BaseQueryResults(object):
    def __init__(self, query):
        self.corpus = query.corpus
        self.call_back = query.call_back
        self.stop_check = query.stop_check
        self.cursors = []
        self.evaluated = []
        self.current_ind = 0
        if query._columns:
            self.cache = self.corpus.execute_cypher(query.cypher(), **query.cypher_params())
            self.models = False
            self._preload = None
            self._to_find = None
            self._to_find_type = None
            self._columns = [x.output_alias.replace('`', '') for x in query._columns]
        else:

            self.cache = self.corpus.execute_cypher(query.cypher(), **query.cypher_params())
            self.models = True
            self._preload = query._preload
            self._to_find = query.to_find.alias
            self._to_find_type = query.to_find.type_alias
            self._columns = None

    @property
    def columns(self):
        return self._columns

    def __str__(self):
        return '\n'.join(str(x) for x in self)

    def __getitem__(self, key):
        if key < 0:
            raise (IndexError('Results do not support negative indexing.'))
        cur_cache_len = len(self.cache)
        if key < cur_cache_len:
            return self._sanitize_record(self.cache[key])
        self._cache_cursor(up_to=key)
        cur_cache_len = len(self.cache)
        if key < cur_cache_len:
            return self._sanitize_record(self.cache[key])
        raise (IndexError(key))

    def _cache_cursor(self, up_to=None):
        for i, c in enumerate(self.cursors):
            if i in self.evaluated:
                continue
            while True:
                try:
                    r = next(c)
                except StopIteration:
                    r = None
                if r is None:
                    self.evaluated.append(i)
                    break
                r = self._sanitize_record(r)
                self.cache.append(r)
                if up_to is not None and len(self.cache) > up_to:
                    break
            if up_to is not None and len(self.cache) > up_to:
                break

    def add_results(self, query):
        ## Add some validation
        cursor = query.all().cache
        self.cache.extend(cursor)

    def next(self, number):
        next_ind = number + self.current_ind
        if next_ind > len(self.cache):
            self._cache_cursor(up_to=next_ind)
        to_return = self.cache[self.current_ind:next_ind]
        self.current_ind = next_ind
        return to_return

    def previous(self, number):
        if number > self.current_ind:
            to_return = self.cache[0:self.current_ind]
            self.current_ind = 0
        else:
            next_ind = self.current_ind - number
            to_return = self.cache[next_ind:self.current_ind]
            self.current_ind = next_ind
        return to_return

    def __iter__(self):
        for r in self.cache:
            yield self._sanitize_record(r)

    def rows_for_csv(self):
        header = self.columns
        for line in self:
            yield {k: line[k] for k in header}

    def to_csv(self, path, mode='w'):
        from ...io import save_results
        save_results(self.rows_for_csv(), path, header=self.columns, mode=mode)

    def to_json(self):
        for line in self:
            baseline = {k: line[k] for k in self.columns}
            yield baseline

    def __len__(self):
        self._cache_cursor()
        return len(self.cache)

    def _sanitize_record(self, r):
        if self.models:
            raise NotImplementedError
        else:
            r = BaseRecord(r)
        return r
