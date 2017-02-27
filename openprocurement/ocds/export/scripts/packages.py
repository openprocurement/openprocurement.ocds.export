# -*- coding: utf-8 -*-
import argparse
import os
import logging
import math
import couchdb.json
import multiprocessing as mp
from functools import partial
from itertools import izip_longest as zip_longest
from simplejson import dump
from jinja2 import (
    Environment,
    PackageLoader
)
from filechunkio import FileChunkIO

from openprocurement.ocds.export.helpers import (
    connect_bucket,
    read_config,
    parse_dates,
    make_zip,
    dump_json,
    file_size,
    get_torrent_link
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
    if end:
        result = [r.doc for r in list(db.view('tenders/all',
                                              startkey=start,
                                              endkey=end,
                                              include_docs=True))]
    else:
        result = [r.doc for r in list(db.view('tenders/all',
                                              startkey=start,
                                              include_docs=True))]
    name = 'release-{0:07d}.json'.format(nth)
    path = config['path']
    try:
        if extensions:
            package = package_tenders_ext(result[:-1], config.get('release'))
            package['uri'] = 'http://{}/merged_with_extensions_{}/{}'.format(
                bucket, max_date, name
            )
        else:
            package = package_tenders(result[:-1], config.get('release'))
            package['uri'] = 'http://{}/merged_{}/{}'.format(
                bucket, max_date, name
            )
    except Exception as e:
        logger.info('Error: {}'.format(e))
        return
    if nth == 1:
        if extensions:
            pretty_package = package_tenders_ext(
                result[:24], config.get('release')
            )
            pretty_package['uri'] = 'http://{}/merged_with_extensions_{}/'\
                                    'example.json'.format(bucket, max_date)
        else:
            pretty_package = package_tenders(
                result[:24], config.get('release')
            )
            pretty_package['uri'] = 'http://{}/merged_{}/'\
                                    'example.json'.format(bucket, max_date)
        logger.info('Dump example.json')
        dump_json(config['path'], 'example.json',
                  pretty_package, pretty=True)
    dump_json(path, name, package)
    logger.info('End {}th dump startdoc={} enddoc={}'.format(nth, start, end))


def put_to_s3(bucket, path, time, extensions=False):
    if extensions:
        dir_name = 'merged_with_extensions_{}'.format(time)
    else:
        dir_name = 'merged_{}'.format(time)
    for file in os.listdir(path):
        aws_path = os.path.join(dir_name, file)
        file_path = os.path.join(path, file)
        if file.split('.')[1] == 'zip':
            mp = bucket.initiate_multipart_upload(aws_path)
            source_size = os.stat(file_path).st_size
            chunk_size = 52428800
            chunk_count = int(math.ceil(source_size / chunk_size))
            for i in range(chunk_count + 1):
                offset = chunk_size * i
                bytes = min(chunk_size, source_size - offset)
                with FileChunkIO(file_path, 'r', offset=offset,
                                 bytes=bytes) as fp:
                    mp.upload_part_from_file(fp, part_num=i + 1)
            mp.complete_upload()
        else:
            key = bucket.new_key(aws_path)
            key.set_contents_from_filename(file_path)


def links(path, skip=['example.json', 'index.html', 'releases.zip']):
    for _file in sorted([f for f in os.listdir(path) if
                        f not in skip]):
        yield {
            'size': file_size(path, _file),
            'link': _file
        }


def create_html(path, config, date, extensions=False):
    template = ENV.get_template('index.html')
    key = 'merged_{}' if not extensions else 'merged_with_extensions_{}'
    torrent_link = get_torrent_link(config.get('bucket'), key.format(date))
    zip_size = file_size(path, 'releases.zip')
    with open(os.path.join(path, 'index.html'), 'w') as stream:
        stream.write(template.render(dict(zip_size=zip_size,
                                          torrent_link=torrent_link,
                                          links=links(path))))


def update_index(bucket):
    template = ENV.get_template('base.html')
    index = ENV.get_template('index.html')
    dirs = [d.name for d in bucket.list('merged', '/')]
    html = template.render(dict(links=[x.strip('/') for x in dirs]))
    bucket.get_key('index.html').set_contents_from_string(html)
    logger.info('Updated base index')
    for path in dirs:
        ctx = [p.name for p in bucket.list(path, '/')
               if not p.name.endswith('html')]
        archive = bucket.get_key(path+'releases.zip')
        size = None
        if archive:
            size = archive.size/1024/1024
        torrent_link = get_torrent_link(bucket.name, path)
        files = sorted([{'link': f.split('/')[1], 'size': bucket.get_key(f).size/1024/1024} for f in ctx],
                       key=lambda x: x.get('link'))
        result = index.render(dict(zip_size=size, torrent_link=torrent_link, links=files))
        bucket.get_key(os.path.join(path, 'index.html')).set_contents_from_string(result)
        logger.info('Updated index in {}'.format(path))


def fetch_ids(db, batch_count):
    return [r['id'] for r in db.view('tenders/all')][::batch_count]


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
        max_date = list(_tenders.get_max_date())[-1].split('T')[0]
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
        create_html(config.get('path'), config, max_date, extensions=args.ext)
        if args.s3 and bucket:
            put_to_s3(bucket, config.get('path'),
                      max_date, extensions=args.ext)
            update_index(bucket)
