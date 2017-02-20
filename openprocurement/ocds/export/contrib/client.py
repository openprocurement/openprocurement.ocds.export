import requests
import requests.adapters
import requests.exceptions
from gevent.pool import Pool
import logging


logger = logging.getLogger(__name__)
VERSION =  'X-Revision-N'
VERSION_HASH = 'X-Revision-Hash'
PREV_VERSION = 'X-Revision-Hash'

class APIClient(object):

    def __init__(self, api_key, api_host, api_version, **options):

        self.base_url = "{}/api/{}".format(api_host, api_version)
        self.session = requests.Session()
        self.session.auth = (api_key, '')
        self.session.headers = {
            "Accept": "applicaiton/json",
            "Content-type": "application/json"
        }
        self.historical = options.get('historical', False)
        resourse = options.get('resourse', 'tenders')
        self.resourse_url = '{}/{}'.format(self.base_url, resourse)
        APIAdapter = requests.adapters.HTTPAdapter(max_retries=5,
                                                   pool_connections=50,
                                                   pool_maxsize=50)
        self.session.mount(self.resourse_url, APIAdapter)

        # retreive a server cookie
        resp = self.session.head("{}/{}".format(self.base_url, 'spore'))
        resp.raise_for_status()

    def get_tenders(self, params=None):
        if not params:
            params = {'feed': 'chages'}
        resp = self.session.get(self.resourse_url, params=params)
        if resp.ok:
            return resp.json()

    def get_tender(self, tender_id, version=''):
        args = dict()
        url = '{}/{}'.format(self.resourse_url, tender_id)
        if self.historical:
            url += '/historical'
            args.update(dict(headers={VERSION: version}))
        args.update(url=url)
        try:
            resp = self.session.get(**args)
            if resp.ok:
                #if self.historical and version and version != resp.headers.get(VERSION, ''):
                #    import pdb;pdb.set_trace()
                #    raise requests.exceptions.HTTPError
                data = resp.json().get('data', '')
                if data:
                    return resp.headers.get(VERSION, ''), data
        except requests.exceptions.HTTPError as e:
            logger.warn('Request failed. Error: {}'.format(e))
        return '', {}


def get_retreive_clients(api_key, api_host, api_version, **kw):
    forward = APIClient(api_key, api_host, api_version, **kw)
    backward = APIClient(api_key, api_host, api_version, **kw)
    origin_cookie = forward.session.cookies
    backward.session.cookies = origin_cookie
    return origin_cookie, forward, backward
