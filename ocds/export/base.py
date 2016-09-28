import simplejson as json
from collections import MutableMapping


class Mapping(MutableMapping):

    def __init__(self, *args, **kwargs):
        for key, val in dict(*args, **kwargs).items():
            self._update(key, val)

    def _update(self, key, value):
        if hasattr(self, '__schema__'):
            cheked = self.__schema__({key: value}).items()
            if cheked:
                key, value = cheked.pop()
            else:
                return
        if isinstance(value, dict):
            self.__dict__[key] = Mapping(value)
        elif isinstance(value, (list, tuple)):
            self.__dict__[key] = []
            for v in value:
                if isinstance(v, dict):
                    self.__dict__[key].append(Mapping(v))
                else:
                    self.__dict__[key].append(v)
        else:
            self.__dict__[key] = value

    def __repr__(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self._update(key, value)

    def __setattr__(self, key, value):
        self._update(key, value)

    def __getarttr__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
