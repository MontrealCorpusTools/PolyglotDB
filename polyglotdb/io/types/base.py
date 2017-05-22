class BaseAnnotation(object):
    pass


class BaseAnnotationType(object):
    annotation_class = BaseAnnotation

    def __init__(self, name, linguistic_type):
        self._list = []
        self.name = name
        self.linguistic_type = linguistic_type
        self.ignored = False
        self.speaker = None
        self.type_property = True
        self.subannotation = False
        self.label = False

    def reset(self):
        """
        resets _list and speaker
        """
        self._list = []
        self.speaker = None

    def add(self, annotations, save=True):
        """
        save annotations  to _list

        Parameters
        ----------
        annotations : list
            the annotations to save

        save : boolean
            defaults to True
        """
        for a in annotations:
            if save or len(self._list) < 10:
                # If save is False, only the first 10 annotations are saved
                self._list.append(self.annotation_class(*a))
                pass

    def __iter__(self):
        for x in self._list:
            yield x

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key):
        return self._list[key]
