# -*- coding: utf-8 -*-
import argparse
import os
import logging
import couchdb.json
import multiprocessing as mp
from functools import partial
from itertools import izip_longest as zip_longest
from simplejson import dump
from jinja2 import (
    Environment,
    PackageLoader
)

from openprocurement.ocds.export.storage import (
    TendersStorage
)
from openprocurement.ocds.export.models import (
    package_tenders
)
from openprocurement.ocds.export.ext.models import (
    package_tenders_ext
)
from openprocurement.ocds.export.helpers import (
    connect_bucket,
    read_config,
    parse_dates,
    make_zip,
    dump_json,
    fetch_ids,
    put_to_s3,
    create_html,
    update_index
)

couchdb.json.use('simplejson')
logger = logging.getLogger('packer')
ENV = Environment(
    loader=PackageLoader('openprocurement.ocds.export', 'templates')
)


def parse_args():
    parser = argparse.ArgumentParser('Release Packages')
    parser.add_argument('-c', '--config',
                        required=True,
                        help="Path to configuration file")
    parser.add_argument('-d', action='append',
                        dest='dates',
                        default=[],
                        help='Start-end dates to generate package')
    parser.add_argument('-n', '--number')
    parser.add_argument('-r', '--records',
                        action='store_true',
                        default=False,
                        help='Generate record too')
    parser.add_argument('-s3',
                        action='store_true',
                        help="Choose to start uploading to aws s3",
                        default=False)
    parser.add_argument('-ext',
                        action='store_true',
                        help='Choose to start dump with extensions',
                        default=False)
    return parser.parse_args()


def fetch_and_dump(config, max_date, params, extensions=False):
    nth, (start, end) = params
    logger.info('Start {}th dump startdoc={}'
                ' enddoc={}'.format(nth, start, end))
    db = TendersStorage(config['tenders_db']['url'],
                        config['tenders_db']['name'])
    bucket = config.get('bucket')
    if not start and not end:
        return

    args = {
        'startkey': start,
        'include_docs': True
    }
    if end:
        args.update(dict(endkey=end))
    result = [r.doc for r in list(db.view('tenders/all', **args))]

    package_func = package_tenders if not extensions else package_tenders_ext
    base_url = 'http://{}/merged_{}/{}' if not extensions \
                   else 'http://{}/merged_with_extensions_{}/{}'

    name = 'release-{0:07d}.json'.format(nth)
    path = config['path']
    try:
        package = package_func(result[:-1], config.get('release'))
        package['uri'] = base_url.format(bucket, max_date, name)
    except Exception as e:
        logger.info('Error: {}'.format(e))
        return
    if nth == 1:
        pretty_package = package_func(
            result[:24], config.get('release')
        )
        pretty_package['uri'] = base_url.format(bucket,
                                                max_date,
                                                'example.json')

        dump_json(config['path'], 'example.json', pretty_package, pretty=True)
    dump_json(path, name, package)
    logger.info('End {}th dump startdoc={} enddoc={}'.format(nth, start, end))


def run():
    args = parse_args()
    config = read_config(args.config)
    bucket = connect_bucket(config)
    _tenders = TendersStorage(config['tenders_db']['url'],
                              config['tenders_db']['name'])
    logger.info('Start packaging')
    if not os.path.exists(config.get('path')):
        os.makedirs(config.get('path'))
    if args.dates:
        datestart, datefinish = parse_dates(args.dates)
        to_release = _tenders.get_between_dates(datestart, datefinish)
        pack = package_tenders(list(to_release), config)
        name = 'release_between_{}_{}'.format(datestart.split('T')[0],
                                              datefinish.split('T')[0])
        with open(os.path.join(config['path'], name, 'w')) as stream:
            dump(pack, stream)
    else:
        max_date = _tenders.get_max_date().split('T')[0]
        total = int(args.number) if args.number else 4096
        key_ids = fetch_ids(_tenders, total)
        logger.info('Fetched key doc ids')
        pool = mp.Pool(mp.cpu_count())
        if args.ext:
            _conn = partial(fetch_and_dump, config, max_date, extensions=True)
        else:
            _conn = partial(fetch_and_dump, config, max_date)
        params = enumerate(
            zip_longest(key_ids, key_ids[1::], fillvalue=''),
            1
        )
        pool.map(_conn, params)
        make_zip('releases.zip', config.get('path'))
        create_html(ENV, config.get('path'), config,
                    max_date, extensions=args.ext)
        if args.s3 and bucket:
            put_to_s3(bucket, config.get('path'),
                      max_date, extensions=args.ext)
            update_index(ENV, bucket)
