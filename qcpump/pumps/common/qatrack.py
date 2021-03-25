import base64
import datetime
import json
import requests
from pypac import PACSession
import time

from qcpump.core.json import QCPumpJSONEncoder
from qcpump.pumps.base import BOOLEAN, STRING, FLOAT
from qcpump.settings import Settings

settings = Settings()

HTTP_CREATED = requests.codes['created']
HTTP_OK = requests.codes['ok']


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
        """Fetch all available qatrack test list names"""
        endpoint = self.construct_api_url("qa/testlists")
        return self.get_qatrack_choices(endpoint, "name")

    def get_qatrack_unit_choices(self):
        """Fetch all available qatrack unit names"""
        endpoint = self.construct_api_url("units/units")
        return self.get_qatrack_choices(endpoint, "name")

    def get_qatrack_choices(self, endpoint, attribute=None, params=None, session=None, results=None):

        session = session or self.get_qatrack_session()
        results = results or []
        params = params or {}
        try:
            resp = session.get(endpoint, params=params)
            if resp.status_code != 200:
                return results

            payload = resp.json()
            results += [obj[attribute] if attribute else obj for obj in payload['results']]
            if payload.get("next"):
                return self.get_qatrack_choices(
                    endpoint=payload['next'],
                    params=params,
                    session=session,
                    results=results,
                )

        except Exception:
            pass

        if attribute:
            results.sort()
        return results


class QATrackFetchAndPost(QATrackAPIMixin):

    def pump(self):

        self.log_info("Starting to pump")
        self.utc_url_cache = {}

        throttle = self.get_config_value("QATrack+ API", "throttle")

        records = self.fetch_records()

        for record in records:

            # don't run a DOS attack on your QATrack+ instance!
            time.sleep(throttle)

            if self.should_terminate():
                return

            record_id = self.id_for_record(record)

            if self._is_already_recorded(record):
                self.log_info(f"Found existing record with id={record_id}.")
                continue

            self.log_debug(f"New record found with id={record_id}")

            payload = self._generate_payload(record)
            if payload is None:
                continue

            upload_response = self._upload_payload(payload)
            if upload_response is None:
                # exception logged in upload_payload
                continue

            if upload_response.status_code != HTTP_CREATED:
                try:
                    err_msg = upload_response.json()
                except json.JSONDecodeError:
                    err_msg = f"No JSON data in response. Status code was {upload_response.status_code}"
                self.log_error(
                    f"Uploading record={record_id} resulted in status code={upload_response.status_code}: "
                    f"{err_msg}"
                )
                continue

            self.log_info(
                f"Successfully recorded record with id={record_id} from {payload['work_completed']}"
            )
        else:
            self.log_info("No new records found")

        self.log_info("Pumping complete")

    def fetch_records(self):
        return []

    def test_list_for_record(self, record):
        """Accept a record to process and return a test list name. Must be overridden in subclasses"""
        raise NotImplementedError

    def qatrack_unit_for_record(self, record):
        """Accept a record to process and return a QATrack+ Unit name. Must be overridden in subclasses"""
        raise NotImplementedError

    def id_for_record(self, record):
        raise NotImplementedError

    def work_datetimes_for_record(self, record):
        now = datetime.datetime.now()
        return now, now + datetime.timedelta(seconds=1)

    def test_values_from_record(self, record):
        return {}

    def comment_for_record(self, record):
        """Implement this in subclasses. Accept a record to process and return a QATrack+ Unit Name"""
        return ""

    def cycle_day_for_record(self, record):
        """Which cycle day is being performed? Use 0 for test lists"""
        return 0

    def _is_already_recorded(self, record):
        """Implement a check to determine whether a record has already been processed or not"""
        session = self.get_qatrack_session()
        url = self.construct_api_url("qa/testlistinstances")
        record_id = self.id_for_record(record)
        try:
            resp = session.get(url, params={'user_key': record_id})
            return resp.json()['count'] >= 1
        except Exception as e:
            self.log_debug(f"Querying API for duplicates failed: {e}")
            return False

    def _generate_payload(self, record):
        """Convert record to json payload suitable for posting to QATrack+ to perform a test list"""

        test_values_from_record = self.test_values_from_record(record)
        utc_url = self._utc_url_for_record(record)
        if not utc_url:
            unit_name = self.qatrack_unit_for_record(record)
            tl_name = self.test_list_for_record(record)
            record_id = self.id_for_record(record)
            self.log_error(
                f"UTC URL for Unit: {unit_name} & Test List: {tl_name} not found. "
                f"Skipping record with id={record_id}."
            )
            return

        work_started, work_completed = self.work_datetimes_for_record(record)
        comment = self.comment_for_record(record)
        day = self.cycle_day_for_record(record)

        payload = {
            'unit_test_collection': utc_url,
            'work_started': work_started,
            'work_completed': work_completed,
            'day': day,
            'tests': test_values_from_record,
        }
        if comment:
            payload['comment'] = comment

        return payload

    def _utc_url_for_record(self, record):
        """Convert a record to the url (using cached value where possible) for performing a UTC"""

        unit_name = self.qatrack_unit_for_record(record)
        test_list_name = self.test_list_for_record(record)
        key = (unit_name, test_list_name)
        if None in key:
            return None
        if key not in self.utc_url_cache:
            self.utc_url_cache[key] = self._generate_utc_url(unit_name, test_list_name)

        return self.utc_url_cache[key]

    def _generate_utc_url(self, unit_name, utc_name):
        """Generate a url for performing a UTC"""

        session = self.get_qatrack_session()

        params = {
            "name": utc_name,
            "unit__name": unit_name,
        }

        try:
            utc_url = self.construct_api_url("qa/unittestcollections")
            resp = session.get(utc_url, params=params)
            if resp.status_code != HTTP_OK:
                self.log_info(
                    f"Calling {utc_url} with params={params} failed with status code {resp.status_code}"
                )
                return
        except Exception:
            self.log_info(f"Calling {utc_url} with params={params} failed")
            return

        results = resp.json()

        if results['count'] > 1:
            self.log_critical(
                f"Searching API for Test List Assignment with parameters {params} "
                "returned more than one result. "
                "Please ensure your Unit & Test List names are unique in QATrack+"
            )
            return
        elif results['count'] == 0:
            self.log_info(
                f"Searching API for Test List Assignment with parameters {params} "
                f"returned no results. Please check this units configuration."
            )
            return

        return results['results'][0]['url']

    def _upload_payload(self, payload):

        session = self.get_qatrack_session()
        session.headers['Content-Type'] = 'application/json'
        tli_url = self.construct_api_url("qa/testlistinstances")
        try:
            data = json.dumps(payload, cls=QCPumpJSONEncoder)
            return session.post(tli_url, data=data)
        except Exception as e:
            self.log_critical(f"Posting data to QATrack+ API failed: {e}")


class QATrackFetchAndPostTextFile(QATrackFetchAndPost):

    def _duplicate_query_params(self, slug, value):
        return {
            'unit_test_info__test__slug': slug,
            'attachments__attachment__icontains': value,
        }

    def test_values_from_record(self, record):
        slug, filename = self.slug_and_value_to_check_for_duplicates(record)
        return {
            slug: {
                "value": record.read_text(),
                "filename": filename,
                "encoding": "text",
            }
        }


class QATrackFetchAndPostBinaryFile(QATrackFetchAndPostTextFile):

    ENCODING = "utf-8"

    def test_values_from_record(self, record):
        slug, filename = self.slug_and_value_to_check_for_duplicates(record)
        value = base64.b64encode(record.read_bytes().decode(self.ENCODING)),
        return {
            slug: {
                "value": value,
                "filename": filename,
                "encoding": "base64",
            }
        }
