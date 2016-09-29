import requests
import requests.adapters
import grequests
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

        # retrieve cookie
        self.session.head("{}/{}".format(self.base_url, 'spore'))

    def get_tenders(self, params=None):
        if not params:
            params = {'feed': 'chages'}
        req = [grequests.get(self.resourse_url,
                             params=params,
                             session=self.session)]

        resp = grequests.map(req)
        for r in resp:
            if r.ok:
                return r.json()
            else:
                logger.warn(
                    'Fail while fetching tenders '
                    'feed with client params: {}'.format(params)
                )
                r.raise_for_status()

    def get_tender(self, tender_id, params=None):
        resp = self.session.get(
            "{}/{}".format(self.resourse_url, tender_id), params=params
        )
        if resp.ok:
            return resp.json()['data']
        else:
            resp.raise_for_status()

    def fetch(self, tender_ids):
        urls = ['{}/{}'.format(self.resourse_url, tender_id['id'])
                for tender_id in tender_ids]
        resp = (grequests.get(url, session=self.session, stream=False)
                for url in urls)
        results = [t.json()['data'] for t in grequests.map(resp, size=10)]
        [r.close() for r in resp]
        return results


def get_retreive_clients(api_key, api_host, api_version):
    forward = APIClient(api_key, api_host, api_version)
    backward = APIClient(api_key, api_host, api_version)

    origin_cookie = forward.session.cookies
    backward.session.cookies = origin_cookie
    return origin_cookie, forward, backward
