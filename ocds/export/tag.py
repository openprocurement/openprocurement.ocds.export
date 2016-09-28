from .base import Mapping
from .schema import (
    tender,
    contract,
    award,
    organization_schema
)


class Tender(Mapping):

    __tag__ = 'tender'
    __schema__ = tender

    def __init__(self, *args, **kwargs):
        super(Tender, self).__init__(dict(*args, **kwargs))
        if self.tenderers:
            self.numberOfTenderers = len(self.tenderers)
        else:
            self.numberOfTenderers = 0


class Award(Mapping):

    __tag__ = 'awards'
    __schema__ = award

    def __init__(self, *args, **kwargs):
        super(Award, self).__init__(dict(*args, **kwargs))


class Contract(Mapping):

    __tag__ = 'contracts'
    __schema__ = contract

    def __init__(self, *args, **kwargs):
        super(Contract, self).__init__(dict(*args, **kwargs))


class Buyer(Mapping):

    __tag__ = 'buyer'
    __schema__ = organization_schema

    def __init__(self, *args, **kwargs):
        self.schema = organization_schema
        super(Buyer, self).__init__(dict(*args, **kwargs))


def Tag(tag, vals):
    for cls in Mapping.__subclasses__():
        if cls.__tag__ == tag:
            return cls(vals)
    return None
