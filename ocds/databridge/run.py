import argparse
import requests
import os.path
import sys
import yaml
import logging
from logging.config import dictConfig
from requests.adapters import HTTPAdapter
from .contrib.workers import Fetch
from .feed import APIRetreiver
from .bridge import APIDataBridge


ADAPTER = HTTPAdapter(pool_maxsize=50, pool_connections=100)
SESSION = requests.Session()
LOGGER = logging.getLogger(__name__)
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
    bridge = APIDataBridge(config)
    bridge.add_workers([Fetch], config)
    bridge.run()
