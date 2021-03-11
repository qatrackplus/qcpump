from pypac import PACSession
from qcpump.pumps.base import BOOLEAN, STRING, FLOAT
from qcpump.settings import Settings
settings = Settings()


class QATrackAPIMixin:

    QATRACK_API_CONFIG = {
        'name': 'QATrack+ API',
        'multiple': False,
        'validation': "validate_qatrack",
        'fields': [
            {
                'name': 'api url',
                'type': STRING,
                'required': True,
                'help': (
                    "Enter the root api url for the QATrack+ instance you want to upload data to. "
                    "For Example http://yourqatrackserver/api"
                ),
                'default': 'https://qatrack.example.com/api',
            },
            {
                'name': 'auth token',
                'type': STRING,
                'required': True,
                'help': "Enter the authorization token for the QATrack+ instance you want to upload data to",
                'default': 'd8a65e755a1f9fe8df40d9a15fcd29565f2504cd',
            },
            {
                'name': 'throttle',
                'type': FLOAT,
                'required': True,
                'default': 0.5,
                'help': (
                    "Enter the minimum interval between data uploads "
                    "(i.e. a value of 1 will allow 1 record per second to be uploded)"
                ),
                'validation': {
                    'min': 0,
                    'max': 60,
                }
            },
            {
                'name': 'verify ssl',
                'type': BOOLEAN,
                'required': False,
                'help': "Disable if you want to bypass SSL certificate checks",
                'default': True,
            },
            {
                'name': 'http proxy',
                'type': STRING,
                'required': False,
                'help': "e.g. http://10.10.1.10:3128 or socks5://user:pass@host:port",
                'default': "",
            },
            {
                'name': 'https proxy',
                'type': STRING,
                'required': False,
                'help': "e.g. https://10.10.1.10:3128 or socks5://user:pass@host:port",
                'default': "",
            },
        ],
    }

    def validate_api_url(self, url):
        if not (url.endswith("api") or url.endswith("api/")):
            return False, "Warning: The API url usually ends in '/api/'"
        return True, ""

    def validate_qatrack(self, values):

        url = values['api url']
        if not url.endswith("/"):
            url += "/"

        url += "auth/"
        try:
            session = self.get_qatrack_session(values)
            resp = session.get(url, allow_redirects=False)
            if resp.status_code == 200:
                valid = True
                msg = "Connected Successfully"
            elif resp.status_code == 302:
                valid = False
                msg = "Server responded with a 302 Redirect. Did you forget the '/api/' on the end or your API URL?"
            else:
                valid = False
                if 'json' in resp.headers['Content-Type']:
                    msg = resp.json()['detail']
                else:
                    msg = str(resp.content) or f"Authorization failed with code {resp.status_code}"

        except Exception as e:
            valid = False
            msg = str(e)

        return valid, msg

    def get_qatrack_session(self, values=None):
        vals = values or self.get_config_values('QATrack+ API')[0]
        s = PACSession()
        s.headers['Authorization'] = f"Token {vals['auth token']}"
        if settings.BROWSER_USER_AGENT:
            s.headers['User-Agent'] = settings.BROWSER_USER_AGENT

        s.verify = vals['verify ssl']
        for prox in ['http', 'https']:
            p = vals[f"{prox} proxy"].strip()
            if p:
                s.proxies[prox] = p
        return s

    def construct_api_url(self, end_point):
        url = self.get_config_value('QATrack+ API', 'api url').strip("/")
        end_point = end_point.strip("/")
        return f"{url}/{end_point}/"

    def get_test_list_choices(self):
        endpoint = self.construct_api_url("qa/testlists")
        return self.get_qatrack_choices(endpoint, "name")

    def get_qatrack_unit_choices(self):
        endpoint = self.construct_api_url("units/units")
        return self.get_qatrack_choices(endpoint, "name")

    def get_qatrack_choices(self, endpoint, attribute, params=None, session=None, results=None):

        session = session or self.get_qatrack_session()
        results = results or []
        params = params or {}
        try:
            resp = session.get(endpoint, params=params)
            if resp.status_code != 200:
                return results

            payload = resp.json()
            results += [obj[attribute] for obj in payload['results']]
            if payload.get("next"):
                return self.get_qatrack_choices(
                    endpoint=payload['next'],
                    params=params,
                    session=session,
                    results=results,
                )

        except Exception:
            pass

        results.sort()
        return results
