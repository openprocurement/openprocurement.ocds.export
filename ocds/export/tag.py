from collections import MutableMapping
from .schema import (
    tender,
    contract,
    award,
    organization_schema
)


class Mapping(MutableMapping):

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'schema'):
            raise NotImplementedError()
        self.__dict__.update(self.schema(dict(*args, **kwargs)))

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__.update(self.schema({key: value}))

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)


class Tender(Mapping):

    __tag__ = 'tender'

    def __init__(self, *args, **kwargs):
        self.schema = tender
        super(Tender, self).__init__(*args, **kwargs)


class Award(Mapping):

    __tag__ = 'awards'

    def __init__(self, *args, **kwargs):
        self.schema = award
        super(Award, self).__init__(*args, **kwargs)


class Contract(Mapping):

    __tag__ = 'contracts'

    def __init__(self, *args, **kwargs):
        self.schema = contract
        super(Contract, self).__init__(*args, **kwargs)


class Buyer(Mapping):

    __tag__ = 'buyer'

    def __init__(self, *args, **kwargs):
        self.schema = organization_schema
        super(Buyer, self).__init__(*args, **kwargs)


def Tag(tag, vals):
    for cls in Mapping.__subclasses__():
        if cls.__tag__ == tag:
            return cls(vals)
    return None
