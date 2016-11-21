from .backends.couch import TendersStorage, ReleasesStorage
from .backends.fs import FSStorage
from .backends.main import MainStorage

__all__ = [TendersStorage, ReleasesStorage, FSStorage, MainStorage]
