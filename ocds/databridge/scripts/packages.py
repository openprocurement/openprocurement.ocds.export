# -*- coding: utf-8 -*-
from ocds.storage.backends.couch import CouchStorage
import argparse
import yaml
import iso8601
import os
from ocds.export.package import Package
from ocds.export.release import get_release_from_tender
from uuid import uuid4
import time
import sys


URI = 'https://fake-url/tenders-{}'.format(uuid4().hex)


def read_config(path):
    with open(path) as cfg:
        config = yaml.load(cfg)
    return config


def parse_args():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config', required=True, help="Path to configuration file")
    parser.add_argument('-d', action='append', dest='dates', default=[], help='Start-end dates to generate package')
    parser.add_argument('-n', '--number')
    return parser.parse_args()


def parse_date(date):
    return iso8601.parse_date(date).isoformat()


def get_releases(gen, info):
    for row in gen:
        try:
            if 'ТЕСТУВАННЯ'.decode('utf-8') not in row['title']:
                release = get_release_from_tender(row, info['prefix'])
                yield release
        except KeyError as e:
            print e
            yield None


def run():
    args = parse_args()
    releases = []
    config = read_config(args.config)
    storage = CouchStorage(config.get('tenders_db'))
    info = config.get('release')
    if args.dates:
        datestart = parse_date(args.dates[0])
        datefinish = parse_date(args.dates[1])
        for release in get_releases(storage.get_tenders_between_dates(datestart, datefinish), info):
            if release:
                releases.append(release)
        data = Package(
            releases,
            info['publisher'],
            info['license'],
            info['publicationPolicy'],
            URI
        )
        if not os.path.exists(config.get('path')):
            os.makedirs(config.get('path'))
        with open('{}/release.json'.format(config.get('path')), 'w') as outfile:
            outfile.write(data.to_json())
    else:
        count = 0
        if not args.number:
            total = 16384
        else:
            total = int(args.number)
        for release in get_releases(storage.get_all(), info):
            sys.stdout.write('{}\r'.format(count))
            sys.stdout.flush()
            if release:
                releases.append(release)
                count += 1
            if count == total:
                package = Package(
                    releases,
                    info['publisher'],
                    info['license'],
                    info['publicationPolicy'],
                    URI
                )
                releases = []
                path = os.path.join(config['path'], 'release-{}.json'.format(time.time()))
                with open(path, 'w') as outfile:
                    outfile.write(package.to_json())
                    count = 0
