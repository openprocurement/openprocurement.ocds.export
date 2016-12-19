# -*- coding: utf-8 -*-
import argparse
import yaml
import iso8601
import os
import time
import sys
import logging
from logging.config import dictConfig
from simplejson import dump
from ocds.export import package_tenders, mode_test
from ocds.storage import TendersStorage
from uuid import uuid4


URI = 'https://fake-url/tenders-{}'.format(uuid4().hex)
Logger = logging.getLogger(__name__)

def read_config(path):
    with open(path) as cfg:
        config = yaml.load(cfg)
    dictConfig(config.get('logging', ''))
    return config


def parse_args():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config', required=True, help="Path to configuration file")
    parser.add_argument('-d', action='append', dest='dates', default=[], help='Start-end dates to generate package')
    parser.add_argument('-n', '--number')
    return parser.parse_args()


def parse_dates(dates):
    return iso8601.parse_date(dates[0]).isoformat(), iso8601.parse_date(dates[1]).isoformat()


def dump_package(tenders, config):
    info = config['release']
    try:
        package = package_tenders(tenders, config.get('release'))
    except Exception as e:
        Logger.info('Error: {}'.format(e))
        return
    path = os.path.join(config['path'], 'release-{}.json'.format(time.time()))
    with open(path, 'w') as outfile:
        dump(package, outfile)


def run():
    args = parse_args()
    releases = []
    config = read_config(args.config)
    _tenders = TendersStorage(config['tenders_db']['url'], config['tenders_db']['name'])
    info = config.get('release')
    Logger.info('Start packaging')
    if not os.path.exists(config.get('path')):
        os.makedirs(config.get('path'))

    if args.dates:
        datestart, datefinish  = parse_dates(args.dates)
        tenders = [t['value'] for t in _tenders.db.view('tenders/byDateModified', startkey=datestart, endkey=datefinish) if t['value'].get('status') not in ['draft']]
        dump_package(tenders, config)
    else:
        count = 0
        total = int(args.number) if args.number else 10000
        tenders = []
        for tender in _tenders:
            tenders.append(tender)
            count += 1
            if count == total:
                Logger.info('dumping {} packages'.format(len(tenders)))
                dump_package(tenders, config)
                count = 0
                tenders = []
        if tenders:
            Logger.info('dumping {} packages'.format(len(tenders)))
            dump_package(tenders, config)
