from collections import defaultdict
import csv
import datetime
import re
from pathlib import Path

import jinja2

from qcpump.pumps.base import BOOLEAN, DIRECTORY, BasePump, INT, STRING
from qcpump.pumps.common.qatrack import QATrackFetchAndPost, slugify

MPC_PATH_RE = re.compile(r"""
     .*                     # preamble like NDS-WKS
     -SN(?P<serial_no>\w+)  # serial number
     -(?P<date>\d\d\d\d\-\d\d\-\d\d\-\d\d\-\d\d\-\d\d)    # YYYY-MM-DD-HH-MM-SS
     -(?P<beam_num>\d\d\d\d)
     -(?P<template>[a-zA-Z]+)       # template e.g. BeamCheckTemplate
     (?P<energy>[\d\.]+)        # energy like 6, 9, 12, 2.5
     (?P<beam_type>[xXeE]+)  # beam type like x, e
     (?P<fff>[fF]+)?        # is FFF or not?
     (?P<hdtse>[HDTSE]+)?      # Whether an HDTSE beam
     (?P<mvkv>[MVkV]+)?
     (?P<enhanced>.*)?      # Whether enhanced test or not e.g. MVkVEnhancedCouch
 """, re.X)

MPC_PATH_RE_OLD = re.compile(r"""
     .*                     # preamble like NDS-WKS
     -SN(?P<serial_no>\w+)  # serial number
     -(?P<date>\d\d\d\d\-\d\d\-\d\d\-\d\d\-\d\d\-\d\d)    # YYYY-MM-DD-HH-MM-SS
     -(?P<beam_num>\d\d\d\d)
     -(?P<energy>[\d\.]+)        # energy like 6, 9, 12, 2.5
     (?P<beam_type>[xXeE]+)  # beam type like x, e
     (?P<fff>[fF]+)?        # is FFF or not?
     (?P<hdtse>[HDTSE]+)?      # Whether an HDTSE beam
     (?P<mvkv>[MVkV]+)?
     -(?P<template>[a-zA-Z]+)       # template e.g. Beam or Geometry
     (?P<enhanced>.*)?
 """, re.X)

DATE_GROUP_FMT = "%Y-%m-%d-%H-%M"

ENH_COUCH_CHECKS = "Enhanced Couch Checks"
ENH_MLC_CHECKS = "Enhanced MLC Checks"
COLL_DEVICES_CHECKS = "Collimation Devices Checks"
BEAM_AND_GEOMETRY_CHECKS = "Beam and Geometry Checks"


def mpc_path_to_meta(path):
    try:
        meta = MPC_PATH_RE.match(str(path)).groupdict()
    except AttributeError:
        meta = MPC_PATH_RE_OLD.match(str(path)).groupdict()
    meta['path'] = path
    meta['date'] = datetime.datetime(*map(int, meta['date'].split("-")))
    meta['fff'] = "FFF" if meta['fff'] else ''
    if meta['fff']:
        meta['beam_type'] = 'FFF'
    elif meta['hdtse']:
        meta['beam_type'] = "HDTSE"
    else:
        meta['beam_type'] = meta['beam_type'].upper()
    meta['enhanced'] = meta['enhanced'] or ''
    meta['mvkv'] = meta['mvkv'] or ''
    meta['hdtse'] = meta['hdtse'] or ''
    meta['template'] = ("%s%s %s" % (meta['template'], meta['mvkv'], meta['enhanced'])).strip(" ")
    return meta


def group_by_meta(metas, window_minutes):
    """Group input meta data records by serial number and date/time window"""
    sn_groups = group_by_sn(metas)
    grouped = {}
    for sn, sn_group in sn_groups.items():
        grouped_by_templates = group_by_template(sn_group)
        grouped[sn] = {}
        for template, templ_group in grouped_by_templates.items():
            window_minutes = window_minutes if do_timewindow_grouping(template) else 0
            grouped_by_dates = group_by_dates(templ_group, window_minutes)
            grouped[sn][template] = grouped_by_dates

    return grouped


def group_by_sn(metas):
    """Group input meta data records by serial numbers"""
    grouped = defaultdict(list)
    for meta in metas:
        grouped[meta['serial_no']].append(meta)
    return grouped


def group_by_template(metas):

    grouped = defaultdict(list)
    for meta in metas:
        grouped[template_group(meta['path'])].append(meta)
    return grouped


def do_timewindow_grouping(template):
    """Only non enhanced checks get grouped together"""
    return template == BEAM_AND_GEOMETRY_CHECKS


def template_group(path):
    p = str(path)
    if "Enhanced" in p and "Couch" in p:
        return ENH_COUCH_CHECKS
    elif "Enhanced" in p and "MLC" in p:
        return ENH_MLC_CHECKS
    elif "Collimation" in p and "Devices" in p:
        return COLL_DEVICES_CHECKS
    return BEAM_AND_GEOMETRY_CHECKS


def group_by_dates(metas, window_minutes):
    """Group input meta data records by date"""

    sorted_by_date = list(sorted(metas, key=lambda m: m['date']))

    cur_date = sorted_by_date[0]['date']
    cur_window = cur_date + datetime.timedelta(minutes=window_minutes)
    cur_window_key = cur_date.strftime(DATE_GROUP_FMT)

    grouped = defaultdict(list)
    for meta in sorted_by_date:
        cur_date = meta['date']
        if cur_date > cur_window:
            cur_window = cur_date + datetime.timedelta(minutes=window_minutes)
            cur_window_key = cur_date.strftime(DATE_GROUP_FMT)
        grouped[cur_window_key].append(meta)

    return grouped


def timestamp_filter(timestamp, cutoff_datetime):
    """Return true if timestamp is greater than cutoff_datetime"""

    return datetime.datetime.fromtimestamp(timestamp) > cutoff_datetime


class QATrackMPCPump(QATrackFetchAndPost, BasePump):

    DISPLAY_NAME = "MPC: QATrack MPC Pump"

    HELP_URL = "https://qcpump.readthedocs.io/en/stable/pumps/mpc.html"

    CONFIG = [
        {
            'name': 'MPC',
            'multiple': False,
            'validation': 'validate_mpc',
            'fields': [
                {
                    'name': 'tds directory',
                    'label': 'TDS Directory',
                    'type': DIRECTORY,
                    'required': True,
                    'help': "Select the TDS directory (e.g. I:\\TDS or \\\\YOURSERVER\\VA_Transer\\TDS)",
                },
                {
                    'name': 'fast search',
                    'label': 'Fast search',
                    'type': BOOLEAN,
                    'required': False,
                    'default': True,
                    'help': (
                        "If checked, the search for Results.csv files will be limited to MPCChecks "
                        "sub directories (i.e. I:\\TDS\\*\\MPCChecks\\**\\*.csv)"
                    ),
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
        {
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
                    'default': (
                        "MPC: {{ check_type }}"
                    )
                },
            ]
        }

    ]

    EXCLUDED_TESTS = [
        "CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf",
        "CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf",
        "CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf",
        "CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf",
        "CollimationDevicesGroup/MLCGroup/MLCPosition0/MLCLeavesA/MLCLeaf",
        "CollimationDevicesGroup/MLCGroup/MLCPosition0/MLCLeavesB/MLCLeaf",
        "CollimationDevicesGroup/MLCGroup/MLCPosition1/MLCLeavesA/MLCLeaf",
        "CollimationDevicesGroup/MLCGroup/MLCPosition1/MLCLeavesB/MLCLeaf",
        "CollimationDevicesGroup/MLCGroup/MLCPosition2/MLCLeavesA/MLCLeaf",
        "CollimationDevicesGroup/MLCGroup/MLCPosition2/MLCLeavesB/MLCLeaf",
        "CollimationDevicesGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf",
        "CollimationDevicesGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf"
    ]

    @property
    def autoskip(self):
        return True

    def validate_mpc(self, values):
        """Ensure that both source and destination directories are set."""

        valid = True
        msg = []
        if not values['tds directory']:
            msg.append("You must set a source TDS directory")
            valid = False
        else:
            try:
                p = Path(values['tds directory'].replace("\\", "/")).absolute()
                if not p.is_dir():
                    valid = False
                    msg.append(f"{values['tds directory']} is not a valid directory")
            except Exception:
                valid = False
                msg.append(f"{values['tds directory']} is not a valid file path")

        return valid, ','.join(msg) or 'OK'

    def validate_test_list(self, values):
        name = values['name'].replace(" ", "")
        if "{{check_type}}" not in name:
            return False, "You must include a '{{ check_type }}' template variable in your test list name"
        return True, "OK"

    def pump(self):
        self._unit_cache = {}
        self._record_meta_cache = {}
        self.set_qatrack_unit_names_to_ids()
        return super().pump()

    def set_qatrack_unit_names_to_ids(self):
        """Fetch all available qatrack unit names.  We are overriding common.qatrack version
        of this because users are not selecting the unit names, instead we're getting
        directly from directory name"""
        self.qatrack_unit_names_to_ids = {}

        endpoint = self.construct_api_url("units/units")
        for unit in self.get_qatrack_choices(endpoint):
            self.qatrack_unit_names_to_ids[unit['name']] = unit['number']

    def fetch_records(self):
        """Return a llist of Path objects representing Results.csv files"""
        source = self.get_config_value("MPC", "tds directory").replace("\\", "/")
        fast_search = self.get_config_value("MPC", 'fast search')
        globber = '*/MPCChecks/**/*.csv' if fast_search else '**/Results.csv'
        date_cutoff = self.history_cutoff_date()
        paths = Path(source).glob(globber)
        paths = [p.absolute() for p in paths if timestamp_filter(p.stat().st_mtime, date_cutoff)]
        grouped = self.group_records(paths)
        filtered = self.filter_records(grouped)
        return filtered

    def history_cutoff_date(self):
        """Return the date before which files should not be considered"""
        days_delta = datetime.timedelta(days=self.get_config_value("MPC", "history days"))
        return datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - days_delta

    def group_records(self, paths):
        metas = [mpc_path_to_meta(p) for p in paths]
        minutes = self.get_config_value('MPC', 'grouping window')
        results_groups = []
        for sn, templ_groups in group_by_meta(metas, minutes).items():
            for templ_group, date_groups in templ_groups.items():
                for date_group, grouped in date_groups.items():
                    results_groups.append((sn, templ_group, date_group, grouped))
        return results_groups

    def filter_records(self, records):
        """Remove any groups which are not older than N minutes. This allows us
        to wait until all beam results are written to disk before uploading"""

        now = datetime.datetime.now()
        cutoff_delta = datetime.timedelta(minutes=self.get_config_value("MPC", "wait time"))
        filtered = []
        for record in records:
            sn, template_type, date, path_metas = record
            max_date = sorted(path_metas, key=lambda m: m['date'], reverse=True)[0]['date']
            cutoff = max_date + cutoff_delta
            if cutoff <= now:
                filtered.append(record)

        return filtered

    def id_for_record(self, record):
        sn, template_type, date, metas = record
        return "QCPump/MPC/%s/%s/%s" % (sn, date, template_type)

    def test_list_for_record(self, record):
        sn, template_type, date, metas = record
        tl_name_template = self.get_config_value("Test List", "name")
        template = jinja2.Template(tl_name_template, undefined=jinja2.StrictUndefined)
        return template.render({'check_type': template_type})

    def comment_for_record(self, record):
        sn, template_type, date, metas = record
        return "Fileset:\n\t%s" % ('\n\t'.join(str(m['path']) for m in metas))

    def qatrack_unit_for_record(self, record):
        """Get unit serial number from record and return qatrack unit name for that unit"""

        if not self._unit_cache:
            endpoint = self.construct_api_url("units/units")
            units = self.get_qatrack_choices(endpoint)
            self._unit_cache = {u['serial_number']: u for u in units}

        sn, template_type, date, group_records = record

        try:
            return self._unit_cache[sn]['name']
        except KeyError:
            self.log_error(f"No QATrack+ Unit found with Serial Number {sn}")

    def test_values_from_record(self, record):
        """Convert all values from the csv files in record to test value
        dictionaries suitable for uploading to QATrack+"""

        test_vals = {}
        sn, template_type, date, metas = record

        include_comment = self.get_config_value('QATrack+ API', 'include comment')

        for meta in metas:

            beam_type = f"{meta['energy']}{meta['beam_type']}"

            for row in self.csv_values(meta['path'].open('r', encoding="utf-8")):
                if not self.include_test(row[0]):
                    continue
                slug = self.slugify(row[0], beam_type)
                test_vals[slug] = {
                    'value': self.test_value(row[1]),
                }
                if include_comment:
                    test_vals[slug]['comment'] = "Threshold: %.3f,Result: %s" % (self.test_value(row[2]), row[3].strip())

        return test_vals

    def csv_values(self, file_):
        with file_ as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            headers = next(reader)  # noqa: F841
            for row in reader:
                yield row

    def include_test(self, test_name):
        """Check if the input test name should be included (excludes e.g. individual leaf results)"""
        for exclude in self.EXCLUDED_TESTS:
            if exclude in test_name:
                return False
        return True

    def slugify(self, test_name, beam_type):
        """Take a test name read from CSV file and return a valid test slug"""
        return slugify(test_name + "_" + beam_type)

    def test_value(self, test_val):
        return float(test_val.strip())

    def work_datetimes_for_record(self, record):
        sn, template_type, date, metas = record
        metas = list(sorted(metas, key=lambda m: m['date']))
        min_date = metas[0]['date']
        max_date = max(metas[-1]['date'], min_date + datetime.timedelta(minutes=1))
        return min_date, max_date
