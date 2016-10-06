from .backends.couch import TendersStorage, ReleasesStorage
from .backends.fs import FSStorage

__all__ = [TendersStorage, ReleasesStorage, FSStorage]
