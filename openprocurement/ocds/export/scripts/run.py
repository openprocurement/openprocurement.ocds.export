from gevent import monkey; monkey.patch_all()
import argparse
import os.path
import sys
import yaml
import logging
import functools
from ocds.storage import TendersStorage, ReleasesStorage
from ..contrib.client import APIClient
from logging.config import dictConfig
from ..bridge import APIDataBridge
from ..helpers import (
    exists_or_modified,
    fetch_tenders,
    fetch_tender_versioned,
    batch_releases,
    save_items
)


logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def run():
    parser = argparse.ArgumentParser('API databridge')
    parser.add_argument('-c', '--config', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print "Not a valid config"
        sys.exit(1)

    with open(args.config) as cfg:
        config = yaml.load(cfg)
    if 'logging' in config:
        dictConfig(config['logging'])
    else:
        logging.basicConfig(level=logging.DEBUG)

    storage = ReleasesStorage(config['releases_db']['url'], config['releases_db']['name'])

    client = APIClient(
        config['api']['api_key'],
        config['api']['api_host'],
        config['api']['api_version']
    )

    #_filter = functools.partial(exists_or_modified, storage)
    _fetch = functools.partial(fetch_tender_versioned, client)
    _batch = functools.partial(batch_releases, config.get('release').get('prefix'))
    _save = functools.partial(save_items, storage)

    bridge = APIDataBridge(config)
    bridge.add_worker(_fetch)
    bridge.add_worker(_batch)
    bridge.add_worker(_save)
    bridge.run()
