from collections import defaultdict
import datetime

import jinja2
import requests

from qcpump.core.db import firebirdsql_query, fdb_query, mssql_query
from qcpump.pumps.base import INT, MULTCHOICE, STRING, BasePump
from qcpump.pumps.common.qatrack import QATrackFetchAndPost
from qcpump.settings import Settings

HTTP_CREATED = requests.codes['created']
HTTP_OK = requests.codes['ok']

DATE_GROUP_FMT = "%Y-%m-%d-%H-%M"

db_queriers = {
    'fdb': fdb_query,
    'firebirdsql': firebirdsql_query,
    'mssql': mssql_query,
}

settings = Settings()


QUERY_META = [
    'work_started',
    'work_completed',
    'comment',
    'machine_id',
    'beamenergy',
    'beamtype',
]


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
        self.dqa_machine_name_to_id = {}
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

        self.dqa_machine_name_to_id = {}
        results = []
        connect_kwargs = self.db_connect_kwargs()
        try:
            uquery = (self.get_pump_path() / "queries" / self.db_type / self.db_version / "machines.sql").read_text()
            q_results = self.querier(connect_kwargs, uquery, fetch_method="fetchallmap")
            for row in q_results:
                name = self.dqa3_machine_to_name(row)
                self.dqa_machine_name_to_id[name] = row['machine_id']
                results.append(name)
            self.log_debug(f"Found Units {', '.join(results)}")
        except Exception as e:
            self.log_error(f"Querying units resulted in an error: {e}")

        return results

    def dqa3_machine_to_name(self, row):
        name = f"{row['room_name']}/" if row['room_name'] else ""
        name += f"{row['machine_name']}"
        return name

    def id_for_record(self, record):
        record['data_key'] = str(record['data_key'])
        return f"QCPump/DQA3/{record['machine_id']}/{record['work_started']}/{record['data_key']}"

    @property
    def unit_map(self):
        return {self.dqa_machine_name_to_id[u['dqa3 name']]: u['unit name'] for u in self.get_config_values("Unit")}

    def qatrack_unit_for_record(self, record):
        return self.unit_map[record['machine_id']]

    def work_datetimes_for_record(self, record):
        return record['work_started'], record['work_started'] + datetime.timedelta(minutes=1)

    def test_values_from_record(self, record):
        return {k.lower(): {'value': v} for k, v in record.items() if k not in QUERY_META}

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
            rows = self.querier(self.db_connect_kwargs(), query, params=params, fetch_method="fetchallmap")
        except Exception as e:
            rows = []
            self.log_critical(f"Failed to query {self.db_type} db in pump: {e}")

        return rows

    def prepare_dqa3_query(self):

        # create enough ? placeholders for configured units
        units = list(self.unit_map.keys())
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


def group_by_machine_dates(rows, window_minutes):
    """Group input meta data records by serial number and date/time window"""
    machine_groups = group_by_machine(rows)
    grouped = {}
    for machine, machine_group in machine_groups.items():
        grouped[machine] = group_by_dates(machine_group, window_minutes)

    return grouped


def group_by_machine(rows):
    """Group input records by machine names"""
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['machine_id']].append(row)
    return grouped


def group_by_dates(rows, window_minutes):
    """Group input data records by date"""

    sorted_by_date = list(sorted(rows, key=lambda m: m['work_started']))

    cur_date = sorted_by_date[0]['work_started']
    cur_window = cur_date + datetime.timedelta(minutes=window_minutes)
    cur_window_key = cur_date.strftime(DATE_GROUP_FMT)

    grouped = defaultdict(list)
    for row in sorted_by_date:
        cur_date = row['work_started']
        if cur_date > cur_window:
            cur_window = cur_date + datetime.timedelta(minutes=window_minutes)
            cur_window_key = cur_date.strftime(DATE_GROUP_FMT)
        grouped[cur_window_key].append(row)

    return grouped


class BaseGroupedDQA3(BaseDQA3):

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
                'default': "Daily QA3 Results",
            },
        ]
    }

    def validate_test_list(self, values):
        name = values['name'].strip()
        if not name:
            return False, "You must set a test list name"
        return True, "OK"

    def fetch_records(self):
        records = super().fetch_records()
        grouped = self.group_records(records)
        filtered = self.filter_records(grouped)
        return filtered

    def group_records(self, rows):
        minutes = self.get_config_value('DQA3Reader', 'grouping window')
        results_groups = []
        for machine, date_groups in group_by_machine_dates(rows, minutes).items():
            for date_group, grouped in date_groups.items():
                results_groups.append((machine, date_group, grouped))
        return results_groups

    def filter_records(self, records):
        """Remove any groups which are not older than N minutes. This allows us
        to wait until all beam results are written to disk before uploading"""

        now = datetime.datetime.now()
        cutoff_delta = datetime.timedelta(minutes=self.get_config_value("DQA3Reader", "wait time"))
        filtered = []
        for record in records:
            machine, date, rows = record
            max_date = sorted(rows, key=lambda m: m['work_started'], reverse=True)[0]['work_started']
            cutoff = max_date + cutoff_delta
            if cutoff <= now:
                filtered.append(record)

        return filtered

    def id_for_record(self, record):
        machine_id, date, rows = record
        data_keys = '/'.join(str(r['data_key']) for r in rows)
        return f"QCPump/DQA3/{machine_id}/{date}/{data_keys}"[:255]

    def test_values_from_record(self, record):
        """Convert all values from the csv files in record to test value
        dictionaries suitable for uploading to QATrack+"""

        machine_id, date, rows = record

        # ensure records are sorted by work_started so any duplicate beams get the value
        # of the last acquired beam
        rows = sorted(rows, key=lambda r: r['work_started'])

        test_vals = {}
        for row in rows:

            energy, beam_type = self.energy_and_beam_type_for_row(row)

            for k, v in row.items():
                if k in QUERY_META:
                    continue

                slug = f'{k}_{energy}{beam_type}'.lower()
                test_vals[slug] = {'value': v}

        return test_vals

    def qatrack_unit_for_record(self, record):
        return self.unit_map[record[0]]

    def work_datetimes_for_record(self, record):
        machine, date, rows = record
        rows = list(sorted(rows, key=lambda r: r['work_started']))
        min_date = rows[0]['work_started']
        max_date = max(rows[-1]['work_started'], min_date + datetime.timedelta(minutes=1))
        return min_date, max_date

    def comment_for_record(self, record):
        machine, date, rows = record
        return ('\n'.join(r.get('comment', '') for r in rows)).strip()

    def test_list_for_record(self, record):
        tl_name_template = self.get_config_value("Test List", "name")
        return tl_name_template


class FirebirdGroupedDQA3(BaseGroupedDQA3, QATrackFetchAndPost, BasePump):

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
                {
                    'name': 'grouping window',
                    'label': 'Results group time interval (min)',
                    'type': INT,
                    'required': True,
                    'default': 20,
                    'help': "Enter the time interval (in minutes) for which results should be grouped together.",
                },
                {
                    'name': 'wait time',
                    'label': 'Wait for results (min)',
                    'type': INT,
                    'required': True,
                    'default': 20,
                    'help': (
                        "Wait this many minutes for more results to be "
                        "written to disk before uploading grouped results"
                    ),
                },
            ],
        },
        QATrackFetchAndPost.QATRACK_API_CONFIG,
        BaseGroupedDQA3.TEST_LIST_CONFIG,
        BaseDQA3.UNIT_CONFIG,
    ]


class AtlasGroupedDQA3(BaseGroupedDQA3, QATrackFetchAndPost, BasePump):

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
                {
                    'name': 'grouping window',
                    'label': 'Results group time interval (min)',
                    'type': INT,
                    'required': True,
                    'default': 20,
                    'help': "Enter the time interval (in minutes) for which results should be grouped together.",
                },
                {
                    'name': 'wait time',
                    'label': 'Wait for results (min)',
                    'type': INT,
                    'required': True,
                    'default': 20,
                    'help': (
                        "Wait this many minutes for more results to be "
                        "written to disk before uploading grouped results"
                    ),
                },
            ],
        },
        QATrackFetchAndPost.QATRACK_API_CONFIG,
        BaseGroupedDQA3.TEST_LIST_CONFIG,
        BaseDQA3.UNIT_CONFIG,
    ]
