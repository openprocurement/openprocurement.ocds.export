# -*- coding: utf-8 -*-
import argparse
import yaml
import iso8601
import os
import logging
import math
import zipfile
import couchdb.json
import multiprocessing as mp
from functools import partial
from itertools import izip_longest
from logging.config import dictConfig
from simplejson import dump
from jinja2 import Environment, PackageLoader
from openprocurement.ocds.export.storage import TendersStorage
from boto.s3 import connect_to_region
from openprocurement.ocds.export.models import package_tenders
from boto.s3.connection import OrdinaryCallingFormat, S3ResponseError
from filechunkio import FileChunkIO


couchdb.json.use('simplejson')
Logger = logging.getLogger(__name__)
ENV = Environment(loader=PackageLoader('openprocurement.ocds.export',
                                       'templates'))
logging.getLogger('boto').setLevel(logging.ERROR)


def connect_bucket(config):
    try:
        conn = connect_to_region(
                    'eu-west-1',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', ''),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
                    calling_format=OrdinaryCallingFormat()
                    )
        return conn.get_bucket(config.get('bucket'))
    except S3ResponseError as e:
        Logger.warn('Unable to connect to s3. Error: {}'.format(e))
        return False


def read_config(path):
    with open(path) as cfg:
        config = yaml.load(cfg)
    dictConfig(config.get('logging', ''))
    return config


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


def parse_dates(dates):
    return (iso8601.parse_date(dates[0]).isoformat(),
            iso8601.parse_date(dates[1]).isoformat())


def make_zip(name, base_dir, skip=[]):
    skip.append(name)
    with zipfile.ZipFile(os.path.join(base_dir, name),
                         'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for f in [f for f in os.listdir(base_dir) if f not in skip]:
            zf.write(os.path.join(base_dir, f))


def fetch_and_dump(config, max_date, params, extensions=False):
    nth, (start, end) = params
    Logger.info('Start {}th dump startdoc={}'
                ' enddoc={}'.format(nth, start, end))
    db = TendersStorage(config['tenders_db']['url'],
                        config['tenders_db']['name'])
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
    try:
        if extensions:
            from openprocurement.ocds.export.ext.models import package_tenders_ext
            package = package_tenders_ext(result[:-1], config.get('release'))
            package['uri'] = 'http://ocds.prozorro.openprocurement.io/merged_with_extensions_{}/{}'.format(max_date, name)
        else:
            package = package_tenders(result[:-1], config.get('release'))
            package['uri'] = 'http://ocds.prozorro.openprocurement.io/merged_{}/{}'.format(max_date, name)
        date = max(map(lambda x: x.get('date', ''), package['releases']))
    except Exception as e:
        Logger.info('Error: {}'.format(e))
        return
    path = os.path.join(config['path'], 'release-{0:07d}.json'.format(nth))
    if nth == 1:
        if extensions:
            pretty_package = package_tenders_ext(result[:24], config.get('release'))
            pretty_package['uri'] = 'http://ocds.prozorro.openprocurement.io/merged_with_extensions_{}/example.json'.format(max_date)
        else:
            pretty_package = package_tenders(result[:24], config.get('release'))
            pretty_package['uri'] = 'http://ocds.prozorro.openprocurement.io/merged_{}/example.json'.format(max_date)
        Logger.info('Dump example.json')
        with open(os.path.join(config['path'], 'example.json'), 'w')\
                as outfile:
            dump(pretty_package, outfile, indent=4)
    with open(path, 'w') as outfile:
        dump(package, outfile)
    Logger.info('End {}th dump startdoc={} enddoc={}'.format(nth, start, end))
    return date


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


def file_size(path, name):
    return (os.stat(os.path.join(path, name)).st_size) / 1000000


def get_torrent_link(bucket, path):
    return 'https://s3-eu-west-1.amazonaws.com/'\
            '{}/{}/releases.zip?torrent'.format(bucket, path)


def create_html(path, config, date, extensions=False):
    template = ENV.get_template('index.html')
    links = []
    skip_files = ['example.json', 'index.html', 'releases.zip']
    for file in sorted([f for f in os.listdir(path) if
                        f not in skip_files]):
        link = {}
        link['size'] = file_size(path, file)
        link['link'] = file
        links.append(link)
    if extensions:
        torrent_link = get_torrent_link(config.get('bucket'),
                                        'merged_{}'.format(date))
    else:
        torrent_link = get_torrent_link(config.get('bucket'),
                        'merged_with_extensions{}'.format(date))
    zip_size = file_size(path, 'releases.zip')
    with open(os.path.join(path, 'index.html'), 'w') as stream:
        stream.write(template.render(dict(zip_size=zip_size,
                                          torrent_link=torrent_link,
                                          links=links)))


def update_index(bucket, time, extensions=False):
    key = bucket.new_key('index.html')
    key.get_contents_to_filename('index.html')
    if extensions:
        dir_name = 'merged_with_extensions_{}'.format(time)
    else:
        dir_name = 'merged_{}'.format(time)
    with open('index.html', 'r+') as f:
        lines = f.readlines()
    lines.insert(lines.index('</ol></body>\n'),
                 "<li><a href='{}'>{}</a></li>\n".format(dir_name, dir_name))
    with open('index.html', 'w') as f:
        f.write(''.join(lines))
    key.set_contents_from_filename('index.html')


def fetch_ids(db, batch_count):
    return [r['id'] for r in db.view('tenders/all')][::batch_count]


def run():
    args = parse_args()
    config = read_config(args.config)
    bucket = connect_bucket(config)
    _tenders = TendersStorage(config['tenders_db']['url'],
                              config['tenders_db']['name'])
    Logger.info('Start packaging')
    if not os.path.exists(config.get('path')):
        os.makedirs(config.get('path'))
    if args.dates:
        datestart, datefinish = parse_dates(args.dates)
        pack = package_tenders(list(_tenders.get_between_dates(datestart, datefinish)), config)
        with open(os.path.join(config['path'],
          'release_between_{}_{}'.format(datestart.split('T')[0],
          datefinish).split('T')[0]), 'w') as stream:
            dump(pack, stream)
    else:
        max_date = list(_tenders.get_max_date())[-1].split('T')[0]
        total = int(args.number) if args.number else 4096
        key_ids = fetch_ids(_tenders, total)
        Logger.info('Fetched key doc ids')
        pool = mp.Pool(mp.cpu_count()*2)
        if args.ext:
            _conn = partial(fetch_and_dump, config, max_date, extensions=True)
        else:
            _conn = partial(fetch_and_dump, config, max_date)
        pool.map(_conn, enumerate(izip_longest(key_ids, key_ids[1::],
                                                           fillvalue=''), 1))
        make_zip('releases.zip', config.get('path'))
        create_html(config.get('path'), config, max_date, extensions=args.ext)
        if args.s3 and bucket:
            put_to_s3(bucket, config.get('path'), max_date, extensions=args.ext)
            update_index(bucket, max_date, extensions=args.ext)
