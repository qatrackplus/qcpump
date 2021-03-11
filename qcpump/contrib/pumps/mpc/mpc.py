import datetime
import re
from pathlib import Path

from qcpump.pumps.base import DIRECTORY, BasePump, INT
from qcpump.pumps.common.qatrack import QATrackAPIMixin


PATH_DATE_RE = re.compile(r".*(\d\d\d\d)-(\d\d)-(\d\d)-(\d\d)-(\d\d).*")


class QATrackMPCPump(QATrackAPIMixin, BasePump):

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
        QATrackAPIMixin.QATRACK_API_CONFIG,
    ]

    def validate_mpc(self, values):
        """Ensure that both source and destination directories are set."""

        valid = bool(values['tds directory'])
        msg = []
        if not values['tds directory']:
            msg.append("You must set a source TDS directory")

        return valid, ','.join(msg) or 'OK'

    def pump(self):

        self.log_debug("Starting to pump")
        terminate = False

        source = self.get_config_value("QATrackMPC", "tds directory")
        paths = list(Path(source).glob("**/Results.csv"))
        for path in paths:
            fname = self.filename_from_path(path, with_ext=False)
            if self.is_already_processed(fname):
                self.log_info(f"Found existing result with filename={fname}")
                continue

            self.log_debug(f"Found path {'/'.join(path.parts[-2:])} from date {payload['work_completed']}")

            payload = self.generate_payload(path)
            if payload is None:
                continue

    def generate_payload(self, path):

        work_started = self.date_from_path(path)
        work_completed = work_started + datetime.timedelta(minutes=1)
        utc_url = self.generate_utc_url(path)
        payload = {
            'unit_test_collection': utc_url,
            'work_started': work_started,
            'work_completed': work_completed,
            'tests': {
                'mpc_upload': {
                    'value': path.read_text(),
                    'filename': self.filename_from_path(path),
                }
            }
        }
        return payload

    def date_from_path(self, path):
        """Pull date out of file path and return datetime object"""
        date_parts = map(int, PATH_DATE_RE.match(str(path)).groups())
        return datetime.datetime(*date_parts)

    def generate_utc_url(self, path):
        return ""

    def filename_from_path(self, path, with_ext=True):
        folder = path.parent.parts[-1]
        if with_ext:
            return f"{folder}_Results.csv"
        return f"{folder}_Results"

    def is_already_processed(self, string_val):

        session = self.get_qatrack_session()
        url = self.construct_api_url("qa/testinstances")
        query_params = {
            'unit_test_info__test__slug': "mpc_upload",
            'attachments__attachment__icontains': string_val,
        }
        try:
            resp = session.get(url, params=query_params)
            return resp.json()['count'] >= 1
        except Exception as e:
            self.log_debug(f"Querying API for duplicates failed: {e}")
            return False
