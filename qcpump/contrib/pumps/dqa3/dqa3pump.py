import datetime

import jinja2
import requests

from qcpump.core.db import firebirdsql_query, fdb_query, mssql_query
from qcpump.pumps.base import INT, MULTCHOICE, STRING, BasePump
from qcpump.pumps.common.qatrack import QATrackFetchAndPost
from qcpump.settings import Settings

HTTP_CREATED = requests.codes['created']
HTTP_OK = requests.codes['ok']

UNKNOWN = object()

db_queriers = {
    'fdb': fdb_query,
    'firebirdsql': firebirdsql_query,
    'mssql': mssql_query,
}

settings = Settings()


class BaseDQA3:

    HELP_URL = "https://qcpump.readthedocs.io/en/stable/pumps/dqa3.html"

    query_parameter = "?"

    TEST_LIST_CONFIG = {
        'name': "Test List",
        'multiple': False,
        'dependencies': ["QATrack+ API"],
        'validation': 'validate_test_list',
        'fields': [
            {
                'name': 'name',
                'type': STRING,
                'required': True,
                'help': "Enter a template for the name of the Test List you want to upload data to.",
                'default': "Daily QA3 Results: {{ energy }}{{ beam_type }}",
            },
        ]
    }

    UNIT_CONFIG = {
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
    }

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
                self.db_version = '.'.join(self.db_version.split(".")[:2])

                trend_query_path = self.get_pump_path() / "queries" / self.db_type / self.db_version / "trend.sql"
                if trend_query_path.is_file():
                    self.dqa3_trend_query = trend_query_path.read_text()
                    return True, f"Successful connection (DB version: {self.db_version})"
                else:
                    errors.append(f"Unknown database type/version={self.db_type}/{self.db_version}")

            except Exception as e:
                errors.append(str(e))

        return False, '\n'.join(errors)

    def validate_units(self, values):
        self.log_debug(f"Validating units {values}")

        if not values['dqa3 name'] or not values['unit name']:
            return False, "Please complete both the DQA3 Name and QATrack+ Unit Name settings"
        return True, "OK"

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

    def get_dqa3_unit_choices(self):
        self.log_debug("Fetching DQA3 unit choices")
        if not self.db_version:
            self.log_debug("DB Version not set yet. Units can not be retrieved.")
            return []

        results = []
        connect_kwargs = self.db_connect_kwargs()
        try:
            uquery = (self.get_pump_path() / "queries" / self.db_type / self.db_version / "machines.sql").read_text()
            results = list(sorted(x[0] for x in self.querier(connect_kwargs, uquery)))
            self.log_debug(f"Found Units {', '.join(results)}")
        except Exception as e:
            self.log_error(f"Querying units resulted in an error: {e}")

        return results

    def id_for_record(self, record):
        record['data_key'] = str(record['data_key'])
        return f"QCPump::DQA3::{record['data_key']}"

    @property
    def unit_map(self):
        return {u['dqa3 name']: u['unit name'] for u in self.get_config_values("Unit")}

    def qatrack_unit_for_record(self, record):
        return self.unit_map[record['dqa3_unit_name']]

    def work_datetimes_for_record(self, record):
        return record['work_started'], record['work_completed']

    def test_values_from_record(self, record):
        meta = [
            'work_completed',
            'work_started',
            'comment',
            'dqa3_unit_name',
            'beamenergy',
            'beamtype',
        ]
        return {k.lower(): {'value': v} for k, v in record.items() if k not in meta}

    def comment_for_record(self, record):
        return record.get('comment') or ""

    @property
    def history_days(self):
        return self.get_config_value("DQA3Reader", "history days")

    @property
    def min_date(self):
        return datetime.datetime.now().date() - datetime.timedelta(days=self.history_days)

    def fetch_records(self):
        try:
            query, params = self.prepare_dqa3_query()
            rows = self.querier(self.db_connect_kwargs(), query, params=params, fetch_method="fetchall")
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

    def test_list_for_record(self, record):
        energy, beam_type = self.energy_and_beam_type_for_row(record)
        tl_name_template = self.get_config_value("Test List", "name")
        template = jinja2.Template(tl_name_template, undefined=jinja2.StrictUndefined)
        context = {'energy': energy, 'beam_type': beam_type}
        return template.render(context)

    def energy_and_beam_type_for_row(self, row):

        dqa_beam_type = row['beamtype'].lower()

        if dqa_beam_type == "fff":
            beam_type = "FFF"
        elif dqa_beam_type == "electron":
            beam_type = "E"
        else:
            beam_type = "X"

        energy = row['beamenergy']
        return energy, beam_type


class FirebirdDQA3(BaseDQA3, QATrackFetchAndPost, BasePump):

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
                    'default': 1,
                    'help': "Enter the number of prior days you want to look for data to import",
                },
            ],
        },
        QATrackFetchAndPost.QATRACK_API_CONFIG,
        BaseDQA3.TEST_LIST_CONFIG,
        BaseDQA3.UNIT_CONFIG,
    ]


class AtlasDQA3(BaseDQA3, QATrackFetchAndPost, BasePump):

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
                    'default': 1,
                    'help': "Enter the number of days you want to import data for",
                },
            ],
        },
        QATrackFetchAndPost.QATRACK_API_CONFIG,
        BaseDQA3.TEST_LIST_CONFIG,
        BaseDQA3.UNIT_CONFIG,
    ]
