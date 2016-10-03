from .backends.couch import CouchStorage
from .backends.fs import FSStorage

__all__ = [CouchStorage, FSStorage]
