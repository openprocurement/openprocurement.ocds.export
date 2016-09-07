from collections import MutableMapping



class Mapping(MutableMapping):

    def __init__(self, *args, **kwargs):
        for key, val in dict(*args, **kwargs).items():
            if isinstance(val, dict):
                self.__dict__[key] = Mapping(val)
            elif isinstance(val, list):
                self.__dict__[key] = []
                for v in val:
                    if isinstance(v, dict):
                        self.__dict__[key].append(Mapping(v))
                    else:
                        self.__dict__[key].append(v)
            else:
                self.__dict__[key] = val

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            self.__dict__[key] = Mapping(value)
        else:
            self.__dict__[key] = value

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            self.__dict__[key] = Mapping(value)
        else:
            self.__dict__[key] = value

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


