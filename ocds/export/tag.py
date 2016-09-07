from .base import Mapping
from .schema import (
    tender,
    contract,
    award,
    organization_schema
)


class Tender(Mapping):

    __tag__ = 'tender'

    def __init__(self, *args, **kwargs):
        super(Tender, self).__init__(tender(dict(*args, **kwargs)))


class Award(Mapping):

    __tag__ = 'awards'

    def __init__(self, *args, **kwargs):
        super(Award, self).__init__(award(dict(*args, **kwargs)))


class Contract(Mapping):

    __tag__ = 'contracts'

    def __init__(self, *args, **kwargs):
        super(Contract, self).__init__(contract(dict(*args, **kwargs)))


class Buyer(Mapping):

    __tag__ = 'buyer'

    def __init__(self, *args, **kwargs):
        self.schema = organization_schema
        super(Buyer, self).__init__(organization_schema(dict(*args, **kwargs)))


def Tag(tag, vals):
    for cls in Mapping.__subclasses__():
        if cls.__tag__ == tag:
            return cls(vals)
    return None
