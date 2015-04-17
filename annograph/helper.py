import numpy as np

class AnnotationType(object):
    def __init__(self, name, subtype, supertype, anchor = False,
                    token = False, base = False,
                    delimited = False, speaker = None):
        self._list = list()
        self.name = name
        self.subtype = subtype
        self.supertype = supertype
        self.token = token
        self.base = base
        self.delimited = delimited
        self.anchor = anchor
        self.speaker = speaker
        if supertype is None:
            self.root = True
        else:
            self.root = False
        if self.speaker is not None:
            self.output_name = re.sub('{}\W*'.format(self.speaker),'',self.name)
        else:
            self.output_name = self.name

    def __getitem__(self, key):
        return self._list[key]

    def add(self, annotations):
        self._list.extend(annotations)

    def __iter__(self):
        for x in self._list:
            yield x

    def __len__(self):
        return len(self._list)

    @property
    def delimiter(self):
        return self.attribute.delimiter

    @property
    def is_word_anchor(self):
        return not self.token and self.anchor

    @property
    def is_token_base(self):
        return self.token and self.base

    @property
    def is_type_base(self):
        return not self.token and self.base

class DiscourseData(object):
    def __init__(self, name, levels):
        self.name = name
        self.data = {x.name: x for x in levels}

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, item):
        return item in self.data

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def collapse_speakers(self):
        newdata = dict()
        shifts = {self.data[x].output_name: 0 for x in self.base_levels}
        #Sort keys by speaker, then non-base levels, then base levels

        keys = list()
        speakers = sorted(set(x.speaker for x in self.data.values() if x.speaker is not None))
        for s in speakers:
            base = list()
            for k,v in self.data.items():
                if v.speaker != s:
                    continue
                if v.base:
                    base.append(k)
                else:
                    keys.append(k)
            keys.extend(base)
        for k in keys:
            v = self.data[k]
            name = v.output_name
            if name not in newdata:
                subtype = v.subtype
                supertype = v.supertype
                if subtype is not None:
                    subtype = self.data[subtype].output_name
                if supertype is not None:
                    supertype = self.data[supertype].output_name
                newdata[v.output_name] = AnnotationType(v.output_name, subtype, supertype,
                    anchor = v.anchor,token = v.token, base = v.base,
                    delimited = v.delimited)
            for ann in v:
                newann = dict()
                for k2,v2 in ann.items():
                    try:
                        newk2 = self.data[k2].output_name
                        newv2 = (v2[0]+shifts[newk2],v2[1]+shifts[newk2])

                    except KeyError:
                        newk2 = k2
                        newv2 = v2
                    newann[newk2] = newv2

                newdata[v.output_name].add([newann])
            if v.base:
                shifts[v.output_name] += len(v)
        self.data = newdata

    @property
    def process_order(self):
        order = self.word_levels
        while len(order) < len(self.data.keys()) - len(self.base_levels):
            for k,v in self.data.items():
                if k in order:
                    continue
                if v.base:
                    continue
                if v.root:
                    order.append(k)
                    continue
                if v.supertype in order:
                    order.append(k)
        return order


    @property
    def word_levels(self):
        levels = list()
        for k in self.data.keys():
            if self.data[k].is_word_anchor:
                levels.append(k)
        return levels

    @property
    def base_levels(self):
        levels = list()
        for k in self.data.keys():
            if self.data[k].base:
                levels.append(k)
        return levels

    def add_annotations(self,**kwargs):
        for k,v in kwargs.items():
            self.data[k].add(v)

    def level_length(self, key):
        return len(self.data[key])

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
        return instance

def align_phones(seqj, seqi, gap=-1, matrix=None, match=1, mismatch=-1):
    """
    """
    UP, LEFT, DIAG, NONE = range(4)
    max_j = len(seqj)
    max_i = len(seqi)
    if matrix is not None:
        matrix = read_matrix(matrix)

    score   = np.zeros((max_i + 1, max_j + 1), dtype='f')
    pointer = np.zeros((max_i + 1, max_j + 1), dtype='i')
    max_i, max_j

    pointer[0, 0] = NONE
    score[0, 0] = 0.0


    pointer[0, 1:] = LEFT
    pointer[1:, 0] = UP

    score[0, 1:] = gap * np.arange(max_j)
    score[1:, 0] = gap * np.arange(max_i)

    for i in range(1, max_i + 1):
        ci = seqi[i - 1]
        for j in range(1, max_j + 1):
            cj = seqj[j - 1]

            if matrix is None:
                diag_score = score[i - 1, j - 1] + (cj['label'] == ci['label'] and match or mismatch)
            else:
                diag_score = score[i - 1, j - 1] + matrix[cj['label']][ci['label']]

            up_score   = score[i - 1, j] + gap
            left_score = score[i, j - 1] + gap

            if diag_score >= up_score:
                if diag_score >= left_score:
                    score[i, j] = diag_score
                    pointer[i, j] = DIAG
                else:
                    score[i, j] = left_score
                    pointer[i, j] = LEFT

            else:
                if up_score > left_score:
                    score[i, j ]  = up_score
                    pointer[i, j] = UP
                else:
                    score[i, j]   = left_score
                    pointer[i, j] = LEFT


    align_j = list()
    align_i = list()
    while True:
        p = pointer[i, j]
        if p == NONE: break
        s = score[i, j]
        if p == DIAG:
            align_j.append(seqj[j - 1])
            align_i.append(seqi[i - 1])
            i -= 1
            j -= 1
        elif p == LEFT:
            align_j.append(seqj[j - 1])
            align_i.append("-")
            j -= 1
        elif p == UP:
            align_j.append("-")
            align_i.append(seqi[i - 1])
            i -= 1
        else:
            raise Exception('wtf!')

    return align_j[::-1], align_i[::-1]
