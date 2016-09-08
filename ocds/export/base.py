from collections import MutableMapping


class Mapping(MutableMapping):

    def __init__(self, *args, **kwargs):
        for key, val in dict(*args, **kwargs).items():
            self._update(key, val)

    def _update(self, key, value):
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

    def unwrap(self):
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Mapping):
                result[k] = v.unwrap()
            else:
                result[k] = v
        return result
