import datetime
import re
from pathlib import Path

import jinja2

from qcpump.pumps.base import DIRECTORY, BasePump, INT, STRING
from qcpump.pumps.common.qatrack import QATrackFetchAndPostTextFile

MPC_PATH_RE = re.compile(r"""
     .*                     # preamble like NDS-WKS
     SN(?P<serial_no>\w+)-  # serial number
     (?P<year>\d\d\d\d)-    # year
     (?P<month>\d\d)-       # month
     (?P<day>\d\d)-         # day
     (?P<hour>\d\d)-        # hour
     (?P<min>\d\d)-         # min
     (?P<sec>\d\d)-         # sec
     (?P<unknown>\d\d\d\d)- # don't know what these 4 digist represent
     (?P<template>.*)       # template e.g. BeamCheckTemplate
     (?P<energy>\d+)        # energy like 6, 9, 12
     (?P<beam_type>[xXeE]+)  # beam type like x, e
     (?P<fff>[fF]+)?        # is FFF or not?
     (?P<enhanced>.*)?      # Whether enhanced test or not e.g. MVkVEnhancedCouch
 """, re.X)


class QATrackMPCPump(QATrackFetchAndPostTextFile, BasePump):

    CONFIG = [
        {
            'name': 'QATrackMPC',
            'multiple': False,
            'validation': 'validate_mpc',
            'fields': [
                {
                    'name': 'tds directory',
                    'label': 'TDS Directory',
                    'type': DIRECTORY,
                    'required': True,
                    'help': "Select the TDS directory (e.g. I:\\TDS)",
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
        QATrackFetchAndPostTextFile.QATRACK_API_CONFIG,
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
                        "MPC: {{ template}}{% if enhanced %} {{ enhanced }}{% endif %} "
                        "{{ energy }}{{ beam_type }}{{ fff }}"
                    )
                },
            ]
        }

    ]

    def validate_mpc(self, values):
        """Ensure that both source and destination directories are set."""

        valid = bool(values['tds directory'])
        msg = []
        if not values['tds directory']:
            msg.append("You must set a source TDS directory")

        return valid, ','.join(msg) or 'OK'

    def validate_test_list(self, values):
        name = values['name'].replace(" ", "")
        required = ["template", "enhanced", "energy", "beam_type", "fff"]
        all_present = all("{{%s}}" % f in name for f in required)
        if not all_present:
            return False, f"You must include template variables for all of the folowing: {', '.join(required)}"
        return True, "OK"

    def pump(self):
        self._unit_cache = {}
        self._record_meta_cache = {}
        return super().pump()

    def fetch_records(self):
        """Return a llist of Path objects representing Results.csv files"""
        source = self.get_config_value("QATrackMPC", "tds directory")
        return [p.absolute() for p in Path(source).glob("**/Results.csv")]

    def slug_and_value_to_check_for_duplicates(self, record):
        fname = self.filename_from_path(record, with_ext=False)
        return "mpc_upload", fname

    def test_list_for_record(self, record):
        meta = self.record_meta(record)
        tl_name_template = self.get_config_value("Test List", "name")
        template = jinja2.Template(tl_name_template, undefined=jinja2.StrictUndefined)
        return template.render(meta)

    def record_meta(self, record):
        try:
            meta = self._record_meta_cache[str(record)]
        except KeyError:
            meta = MPC_PATH_RE.match(record).groupdict()
            meta['fff'] = "FFF" if meta['fff'] else ''
            meta['beam_type'] = meta['beam_type'].upper()
            self._record_meta_cache[str(record)] = meta

        return meta

    def record_serial_no(self, record):
        return self.record_meta(record)['serial_no']

    def record_date(self, record):
        m = self.record_meta(record)
        return datetime.datetime(m['year'], m['month'], m['day'], m['hour'], m['min'], m['sec'])

    def qatrack_unit_for_record(self, record):
        """Get unit serial number from record and return qatrack unit name for that unit"""

        if not self._unit_cache:
            endpoint = self.construct_api_url("units/units")
            units = self.get_qatrack_choices(endpoint)
            self._unit_cache = {u['serial_number']: u for u in units}

        sn = self.record_serial_no()

        try:
            return self._unit_cache[sn]['name']
        except KeyError:
            self.log_error(f"No QATrack+ Unit found with Serial Number {sn}")

    def work_datetimes_for_record(self, record):
        """Pull date out of file path and return datetime object"""
        work_started = self.record_date(record)
        work_completed = work_started + datetime.timedelta(seconds=1)
        return work_started, work_completed

    def filename_from_path(self, path, with_ext=True):
        folder = path.parent.parts[-1]
        if with_ext:
            return f"{folder}_Results.csv"
        return f"{folder}_Results"
