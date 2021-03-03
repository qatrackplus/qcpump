import datetime
import json
import time

import jinja2
import requests

from qcpump.core.db import firebirdsql_query, fdb_query, mssql_query
from qcpump.core.json import QCPumpJSONEncoder
from qcpump.pumps.base import BOOLEAN, INT, MULTCHOICE, STRING, BasePump, FLOAT

HTTP_CREATED = requests.codes['created']
HTTP_OK = requests.codes['ok']

UNKNOWN = object()

db_queriers = {
    'fdb': fdb_query,
    'firebirdsql': firebirdsql_query,
    'mssql': mssql_query,
}


class BaseDQA3:

    query_parameter = "?"

    def __init__(self, *args, **kwargs):

        self.db_version = None
        super().__init__(*args, **kwargs)

    @property
    def querier(self):
        if self.db_type == "mssql":
            return db_queriers[self.db_type]
        return db_queriers[self.get_config_value("DQA3Reader", "driver")]

    def validate_test_list(self, values):
        name = values['name'].replace(" ", "")
        if "{{beam_type}}" not in name or "{{energy}}" not in name:
            msg = (
                "You must include template variables for energy & beam_type e.g. "
                "'Daily QA3 Results: {{ energy }}{{ beam_type }}'"
            )
            return False, msg
        data_key = values['data key test name']
        if not data_key:
            msg = "You must include the name of the QATrack+ test used for tracking the DQA3 data key"
            return False, msg
        return True, "OK"

    def validate_dqa3reader(self, values):
        errors = []
        host = values['host']
        if not host:
            errors.append("Please set a value for the host setting (default is 'localhost')")

        port = values['port']
        if not port:
            errors.append("Please set a value for the port setting (default is '3050')")

        user = values['user']
        password = values['password']
        if not (user and password):
            errors.append("Please set both the user and password fields")

        database = values['database']
        if not database:
            errors.append("Please set the name of the database")

        self.db_version = None
        self.dqa3_trend_query = ""
        if not errors:
            connect_kwargs = self.db_connect_kwargs()

            version_query = (self.get_pump_path() / "queries" / self.db_type / "db_version.sql").read_text()
            try:
                self.db_version = self.querier(connect_kwargs, version_query)[0][0]

                trend_query_path = self.get_pump_path() / "queries" / self.db_type / self.db_version / "trend.sql"
                if trend_query_path.is_file():
                    self.dqa3_trend_query = trend_query_path.read_text()
                    return True, f"Successful connection (DB version: {self.db_version})"
                else:
                    errors.append(f"Unknown database type/version={self.db_type}/{self.db_version}")

            except Exception as e:
                errors.append(str(e))

        return False, '\n'.join(errors)

    def db_connect_kwargs(self):

        config = self.get_config_values('DQA3Reader')[0]

        base_kwargs = {
            'host': config['host'],
            'driver': config['driver'],
            'port': config['port'],
            'database': config['database'],
            'user': config['user'],
            'password': config['password'],
        }

        connect_kwargs = {}
        for default_name, value in base_kwargs.items():
            driver_specific = self.db_kwargs_to_connect_kwargs.get(config['driver'], {})
            name = driver_specific.get(default_name, 0)
            if name is not None:
                new_name = default_name if name == 0 else name
                connect_kwargs[new_name] = value

        return connect_kwargs

    def validate_api_url(self, url):
        if not (url.endswith("api") or url.endswith("api/")):
            return False, "Warning: The API url usually ends in '/api/'"
        return True, ""

    def validate_units(self, values):
        self.log_debug(f"Validating units {values}")

        if values['dqa3 name'] in (None, '') or values['unit name'] in (None, ''):
            return False, "Please complete both the DQA3 Name & QATrack+ Unit Name settings"
        return True, "OK"

    def validate_qatrack(self, values):

        url = values['api url']
        if not url.endswith("/"):
            url += "/"

        url += "auth/"

        token = values['auth token']
        verify_ssl = values['verify ssl']

        headers = {'Authorization': f"Token {token}"}
        try:
            resp = requests.get(url, headers=headers, verify=verify_ssl, allow_redirects=False)
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

    def get_qatrack_session(self):
        vals = self.get_config_values('QATrack+ API')[0]
        s = requests.Session()
        s.headers.update({'Authorization': f"Token {vals['auth token']}"})
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

    def get_dqa3_unit_choices(self):
        self.log_debug("Fetching DQA3 unit choices")
        if not self.db_version:
            self.log_debug("DB Version not set yet. Units can not be retrieved.")
            return []

        results = []
        connect_kwargs = self.db_connect_kwargs()
        try:
            uquery = (self.get_pump_path() / "queries" / self.db_type / self.db_version / "machines.sql").read_text()
            results = [x[0] for x in self.querier(connect_kwargs, uquery)]
            self.log_debug(f"Found Units {', '.join(results)}")
        except Exception as e:
            self.log_error(f"Querying units resulted in an error {e}")

        return results

    def pump(self):

        self.log_info("Starting to pump")

        self.utc_url_cache = {}
        throttle = self.get_config_value("QATrack+ API", "throttle")

        for row in self.dqa3_results():

            # don't run a DOS attack on your QATrack+ instance!
            time.sleep(throttle)

            data_key = row['data_key']

            if self.should_terminate():
                return

            energy, beam_type = self.energy_and_beam_type_for_row(row)

            if self.is_already_processed(row):
                self.log_info(
                    f"Found existing result with data_key={data_key} for "
                    f"{energy}{beam_type} from {row['work_completed']}"
                )
                continue

            self.log_debug(f"New record found with data_key={data_key}")

            payload = self.generate_payload(row)
            if payload is None:
                continue

            upload_response = self.upload_payload(payload)
            if upload_response is None:
                # exception logged in upload_payload
                continue

            if upload_response.status_code != HTTP_CREATED:
                try:
                    err_msg = upload_response.json()
                except json.JSONDecodeError:
                    err_msg = f"No JSON data in response. Status code was {upload_response.status_code}"
                self.log_error(
                    f"Uploading data_key={data_key} resulted in status code={upload_response.status_code}: "
                    f"{err_msg}"
                )
                continue

            self.log_info(
                f"Successfully recorded data_key={data_key} for {energy}{beam_type} from {row['work_completed']}"
            )
        else:
            units = ', '.join(self.unit_map.keys())
            self.log_info(
                f"No new records found for units: {units} in last {self.history_days} days (since {self.min_date})"
            )

        self.log_info("Pumping complete")

    @property
    def unit_map(self):
        return {u['dqa3 name']: u['unit name'] for u in self.get_config_values("Unit")}

    @property
    def history_days(self):
        return self.get_config_value("DQA3Reader", "history days")

    @property
    def min_date(self):
        return datetime.datetime.now().date() - datetime.timedelta(days=self.history_days)

    def dqa3_results(self):
        try:
            query, params = self.prepare_dqa3_query()
            rows = self.dqa3_query(query, params, "fetchallmap")
        except Exception as e:
            rows = []
            self.log_critical(f"Failed to query {self.db_type} db in pump: {e}")

        return rows

    def prepare_dqa3_query(self):

        # create enough ? placeholders for configured units
        units = ["%s" % dqa3_unit_name for dqa3_unit_name in self.unit_map.keys()]
        unit_placeholders = ','.join(self.query_parameter for __ in units)
        q = self.dqa3_trend_query.format(units=unit_placeholders)
        return q, [self.min_date] + units

    def dqa3_query(self, statement, params=None, fetch_method="fetchall"):
        return self.querier(self.db_connect_kwargs(), statement, params=params, fetch_method=fetch_method)

    def generate_payload(self, row):
        self.log_debug(f"Starting to generate payload for row with data_key={row['data_key']}")

        unit_name = self.unit_map.get(row['dqa3_unit_name'])
        if unit_name is None:
            self.log_info(f"Missing config for DQA3 Machine '{row['dqa3_unit_name']}'")
            return

        data_key = row['data_key']
        energy, beam_type = self.energy_and_beam_type_for_row(row)
        utc_url = self.get_utc_url(unit_name, energy, beam_type)
        if not utc_url:
            tl_name = self.test_list_name(energy, beam_type)
            self.log_error(
                f"UTC URL for Unit: {unit_name} & Test List: {tl_name} not found. "
                f"Skiping record with data_key={data_key}."
            )
            return

        meta = [
            'work_completed',
            'work_started',
            'comment',
            'dqa3_unit_name',
            'beamenergy',
            'beamtype',
        ]
        r = row
        payload = {
            'unit_test_collection': utc_url,
            'work_started': r['work_started'],
            'work_completed': r['work_completed'],
            'tests': {k.lower(): {
                'value': v
            } for k, v in r.items() if k not in meta}
        }
        if r['comment']:
            payload['comment'] = r['comment']

        self.log_debug(f"Payload generated: {payload}")
        return payload

    def get_utc_url(self, unit_name, energy, beam_type):

        key = (unit_name, energy, beam_type)
        if key not in self.utc_url_cache:
            self.utc_url_cache[key] = self.generate_utc_url(*key)

        return self.utc_url_cache[key]

    def generate_utc_url(self, unit_name, energy, beam_type):

        session = self.get_qatrack_session()

        params = {
            "test_list__name": self.test_list_name(energy, beam_type),
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

    def test_list_name(self, energy, beam_type):

        tl_name_template = self.get_config_value("Test List", "name")
        template = jinja2.Template(tl_name_template, undefined=jinja2.StrictUndefined)
        context = {'energy': energy, 'beam_type': beam_type}
        return template.render(context)

    def energy_and_beam_type_for_row(self, row):
        beam_type = 'X' if row['beamtype'].lower() == "photon" else 'E'
        energy = row['beamenergy']
        return energy, beam_type

    def is_already_processed(self, row):

        session = self.get_qatrack_session()

        url = self.construct_api_url("qa/testinstances")
        energy, beam_type = self.energy_and_beam_type_for_row(row)
        tl_name = self.test_list_name(energy, beam_type)
        test_name = self.get_config_value('Test List', 'data key test name')
        query_params = {
            'test_list_instance__test_list__name': tl_name,
            'unit_test_info__test__name': test_name,
            'string_value': str(row['data_key']),
        }
        try:
            resp = session.get(url, params=query_params)
            return resp.json()['count'] >= 1
        except Exception as e:
            self.log_debug(f"Querying API for duplicates failed: {e}")
            return False

    def upload_payload(self, payload):

        session = self.get_qatrack_session()
        session.headers['Content-Type'] = 'application/json'
        tli_url = self.construct_api_url("qa/testlistinstances")
        try:
            data = json.dumps(payload, cls=QCPumpJSONEncoder)
            return session.post(tli_url, data=data)
        except Exception as e:
            self.log_critical(f"Posting data to QATrack+ API failed: {e}")


class FirebirdDQA3(BaseDQA3, BasePump):

    query_parameter = "?"
    db_type = "fdb"

    db_kwargs_to_connect_kwargs = {
        'fdb': {
            'driver': None,
        },
        'firebirdsql': {
            'driver': None,
        },
    }

    CONFIG = [
        {
            'name': 'DQA3Reader',
            'multiple': False,
            'validation': 'validate_dqa3reader',
            'fields': [
                {
                    'name': 'host',
                    'type': STRING,
                    'required': True,
                    'help': "Enter the host name of the database server you want to connect to",
                    'default': 'localhost'
                },
                {
                    'name': 'database',
                    'label': "Database File Path",
                    'type': STRING,
                    'required': True,
                    'help': (
                        "Enter the path to the database file you want to connect to on the server."
                        r" For example C:\Users\YourUserName\databases\Sncdata.fdb"
                    ),
                },
                {
                    'name': 'user',
                    'type': STRING,
                    'required': True,
                    'default': 'sysdba',
                    'help': "Enter the username you want to use to connect to the database with",
                },
                {
                    'name': 'password',
                    'type': STRING,
                    'required': True,
                    'default': 'masterkey',
                    'help': "Enter the password you want to use to connect to the database with",
                },
                {
                    'name': 'port',
                    'type': INT,
                    'required': False,
                    'default': 3050,
                    'help': "Enter the port number that the Firebird Database server is listening on",
                    'validation': {
                        'min': 0,
                        'max': 2**16 - 1,
                    }
                },
                {
                    'name': 'driver',
                    'type': MULTCHOICE,
                    'required': True,
                    'help': "Select the database driver you want to use",
                    'default': 'firebirdsql',
                    'choices': ['firebirdsql', 'fdb'],
                },
                {
                    'name': 'history days',
                    'label': 'Days of history',
                    'type': INT,
                    'required': False,
                    'default': 28,
                    'help': "Enter the number of days you want to import data for",
                },
            ],
        },
        {
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
                    'default': '97qf5be0362ef907dba79c24a31a6ndeobbnef54',
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
        },
        {
            'name': "Test List",
            'multiple': False,
            'dependencies': ['QATrack+ API'],
            'validation': 'validate_test_list',
            'fields': [
                {
                    'name': 'name',
                    'type': STRING,
                    'required': True,
                    'help': "Enter a template for the name of the Test List you want to upload data to.",
                    'default': "Daily QA3 Results: {{ energy }}{{ beam_type }}",
                },
                {

                    'name': 'data key test name',
                    'type': STRING,
                    'required': True,
                    'help': "The name of the QATrack+ Test used for tracking which DQA3 Record was uploaded",
                    'default': "DQA3 Results: Data Key",
                },
            ]
        },
        {
            'name': 'Unit',
            'multiple': True,
            'dependencies': ["DQA3Reader", 'QATrack+ API'],
            'validation': 'validate_units',
            'fields': [
                {
                    'name': 'dqa3 name',
                    'type': MULTCHOICE,
                    'required': True,
                    'help': "Enter the name of the unit in the DQA3 database",
                    'choices': 'get_dqa3_unit_choices',
                },
                {
                    'name': 'unit name',
                    'label': "QATrack+ Unit Name",
                    'type': MULTCHOICE,
                    'required': True,
                    'help': "Enter the corresponding name of the unit in the QATrack+ database",
                    'choices': 'get_qatrack_unit_choices',
                },
            ],
        },
    ]


class AtlasDQA3(BaseDQA3, BasePump):

    query_parameter = "?"
    db_type = "mssql"

    db_kwargs_to_connect_kwargs = {
        'py-tds': {
            'host': 'dsn',
        },
        'FreeTDS': {
            'host': 'server',
        },
        'ODBC Driver 17 for SQL Server': {
            'host': 'server',
        },
        'SQL Server Native Client 11.0': {
            'host': 'server',
        },
    }

    CONFIG = [
        {
            'name': 'DQA3Reader',
            'multiple': False,
            'validation': 'validate_dqa3reader',
            'fields': [
                {
                    'name': 'host',
                    'type': STRING,
                    'required': True,
                    'help': "Enter the host name of the database server you want to connect to",
                    'default': 'localhost'
                },
                {
                    'name': 'database',
                    'label': "Database Name",
                    'type': STRING,
                    'required': True,
                    'help': (
                        "Enter the name of the database you want to connect to on the server."
                        r" For example 'atlas'"
                    ),
                },
                {
                    'name': 'user',
                    'type': STRING,
                    'required': True,
                    'default': 'sa',
                    'help': "Enter the username you want to use to connect to the database with",
                },
                {
                    'name': 'password',
                    'type': STRING,
                    'required': True,
                    'default': 'Password123',
                    'help': "Enter the password you want to use to connect to the database with",
                },
                {
                    'name': 'port',
                    'type': INT,
                    'required': False,
                    'default': 1433,
                    'help': "Enter the port number that the Firebird Database server is listening on",
                    'validation': {
                        'min': 0,
                        'max': 2**16 - 1,
                    }
                },
                {
                    'name': 'driver',
                    'type': MULTCHOICE,
                    'required': True,
                    'help': "Select database driver you want to use",
                    'default': 'ODBC Driver 17 for SQL Server',
                    'choices': ['ODBC Driver 17 for SQL Server', 'py-tds', 'FreeTDS', 'SQL Server Native Client 11.0'],
                },
                {
                    'name': 'history days',
                    'label': 'Days of history',
                    'type': INT,
                    'required': False,
                    'default': 28,
                    'help': "Enter the number of days you want to import data for",
                },
            ],
        },
        {
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
                    'default': '97qf5be0362ef907dba79c24a31a6ndeobbnef54',
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
        },
        {
            'name': "Test List",
            'multiple': False,
            'dependencies': ['QATrack+ API'],
            'validation': 'validate_test_list',
            'fields': [
                {
                    'name': 'name',
                    'type': STRING,
                    'required': True,
                    'help': "Enter a template for the name of the Test List you want to upload data to.",
                    'default': "Daily QA3 Results: {{ energy }}{{ beam_type }}",
                },
                {

                    'name': 'data key test name',
                    'type': STRING,
                    'required': True,
                    'help': "The name of the QATrack+ Test used for tracking which DQA3 Record was uploaded",
                    'default': "DQA3 Results: Data Key",
                },
            ]
        },
        {
            'name': 'Unit',
            'multiple': True,
            'dependencies': ["DQA3Reader", 'QATrack+ API'],
            'validation': 'validate_units',
            'fields': [
                {
                    'name': 'dqa3 name',
                    'type': MULTCHOICE,
                    'required': True,
                    'help': "Enter the name of the unit in the DQA3 database",
                    'choices': 'get_dqa3_unit_choices',
                },
                {
                    'name': 'unit name',
                    'label': "QATrack+ Unit Name",
                    'type': MULTCHOICE,
                    'required': True,
                    'help': "Enter the corresponding name of the unit in the QATrack+ database",
                    'choices': 'get_qatrack_unit_choices',
                },
            ],
        },
    ]
