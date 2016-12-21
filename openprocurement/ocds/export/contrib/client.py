import requests
import requests.adapters
from gevent.pool import Pool
import logging


logger = logging.getLogger(__name__)


class APIClient(object):

    def __init__(self, api_key, api_host, api_version, **options):

        self.base_url = "{}/api/{}".format(api_host, api_version)

        self.session = requests.Session()
        self.session.auth = (api_key, '')
        self.session.headers = {"Accept": "applicaiton/json",
                                "Content-type": "application/json"}
        resourse = options.get('resourse', 'tenders')
        self.resourse_url = "{}/{}".format(self.base_url, resourse)
        APIAdapter = requests.adapters.HTTPAdapter(max_retries=5,
                                                   pool_connections=50,
                                                   pool_maxsize=30)
        self.session.mount(self.resourse_url, APIAdapter)
        self.session.head("{}/{}".format(self.base_url, 'spore'))
        self.pool = Pool(10)

    def get_tenders(self, params=None):
        if not params:
            params = {'feed': 'chages'}
        resp = self.session.get(self.resourse_url, params=params)
        if resp.ok:
            return resp.json()
        else:
            resp.raise_for_status()

    def get_tender(self, tender_id, version=''):
        version_header = 'X-Revision-N'
        args = dict(url="{}/{}".format(self.resourse_url, tender_id))
        if version and version.isdigit():
            args.update(dict(headers={version_header: version}))
        resp = self.session.get(**args)
        if resp.ok:
            return resp.headers.get(version_header, ''), resp.json()['data']
        else:
            resp.raise_for_status()

    def fetch(self, tender_ids):
        resp = self.pool.map(self.get_tender, [t['id'] for t in tender_ids])
        return [r for v, r in resp if r]


def get_retreive_clients(api_key, api_host, api_version):
    forward = APIClient(api_key, api_host, api_version)
    backward = APIClient(api_key, api_host, api_version)
    origin_cookie = forward.session.cookies
    backward.session.cookies = origin_cookie
    return origin_cookie, forward, backward
