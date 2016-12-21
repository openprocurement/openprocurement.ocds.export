# -*- coding: utf-8 -*-
import logging
from logging.config import dictConfig
import argparse
import yaml
import os
import sys
from openprocurement.ocds.export.helpers import mode_test
from openprocurement.ocds.export.storage import (
    TendersStorage,
    ReleasesStorage,
    Release,
    release_tender
)


Logger = logging.getLogger(__name__)


def read_config(path):
    with open(path) as cfg:
        config = yaml.load(cfg)
    dictConfig(config.get('logging', ''))
    return config


def parse_args():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config', required=True, help="Path to configuration file")
    return parser.parse_args()


def run():
    args = parse_args()
    config = read_config(args.config)
    info = config.get('release')
    Logger.info('Start generation releases')
    tenders = TendersStorage(config['tenders_db']['url'], config['tenders_db']['name'])
    releases = ReleasesStorage(config['releases_db']['url'], config['releases_db']['name'])

    Logger.info('Connected to databases')
    count = 0
    for tender in tenders:
        Logger.info('Parsed {} docs'.format(count))
        try:
            if mode_test(tender):
                release = release_tender(tender, info['prefix'])
                release.store(releases)
                count += 1
        except KeyError as e:
            Logger.fatal(e)
