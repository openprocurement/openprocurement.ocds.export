import os
import os.path
import logging
import datetime
from .base import Storage
from ocds.storage.errors import InvalidPath


logger = logging.getLogger(__name__)


class FSStorage(Storage):

    def __init__(self, base_path):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            logger.warn('Initial path not exists. Creating')
            try:
                os.makedirs(self.base_path)
            except (IOError, OSError) as e:
                logger.error("Couldn't create destination dir."
                             "Error {}".format(e))
                raise InvalidPath('Not destination folder')

    def _from_string(self, string):
        return datetime.datetime.strptime('%Y-%m-%dT%H:%M:$S')

    def _path_from_date(self, date):
        if isinstance(date, str):
            path = 

