import io
from datetime import datetime as dt, timedelta
from unittest import mock

import pytest
import wx

from qcpump.contrib.pumps.mpc import mpc

dir_name_metas = [
    (
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
        {
            'path': "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
            'serial_no': '1234',
            'date': dt(2020, 11, 6, 9, 59, 21),
            'beam_num': "0009",
            "energy": '6',
            'beam_type': 'X',
            'fff': '',
            'mvkv': 'MVkV',
            'hdtse': '',
            'template': 'GeometryCheckTemplateMVkV',
            'enhanced': ''
        }
    ),
    (
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
        {
            'path': "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
            'serial_no': '1234',
            'date': dt(2020, 11, 6, 9, 59, 21),
            'beam_num': "0007",
            "energy": '16',
            'beam_type': 'E',
            'fff': '',
            'mvkv': '',
            'hdtse': '',
            'template': 'BeamCheckTemplate',
            'enhanced': ''
        },
    ),
    (

        "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
        {
            'path': "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
            'serial_no': '1234',
            'date': dt(2020, 11, 6, 9, 59, 21),
            'beam_num': "0000",
            "energy": '6',
            'beam_type': 'FFF',
            'fff': 'FFF',
            'mvkv': '',
            'hdtse': '',
            'template': 'BeamCheckTemplate',
            'enhanced': ''
        },
    ),
    (
        "NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
        {
            'path': "NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
            'serial_no': '1234',
            'date': dt(2020, 9, 30, 9, 15, 17),
            'beam_num': "0011",
            "energy": '6',
            'beam_type': 'X',
            'fff': '',
            'mvkv': '',
            'hdtse': '',
            'template': 'EnhancedMLCCheckTemplate',
            'enhanced': ''
        }
    ),
    (
        "NDS-WKS-SN1234-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
        {
            'path': "NDS-WKS-SN1234-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
            'serial_no': '1234',
            'date': dt(2020, 10, 1, 11, 26, 55),
            'beam_num': "0010",
            "energy": '6',
            'beam_type': 'X',
            'fff': '',
            'mvkv': 'MVkV',
            'hdtse': '',
            'template': 'GeometryCheckTemplateMVkV EnhancedCouch',
            'enhanced': 'EnhancedCouch'
        },
    ),
    (
        "NDS-WKS-SN7890-2020-10-02-09-08-58-0009-BeamCheckTemplate6eHDTSE",
        {
            'path': "NDS-WKS-SN7890-2020-10-02-09-08-58-0009-BeamCheckTemplate6eHDTSE",
            'serial_no': '7890',
            'date': dt(2020, 10, 2, 9, 8, 58),
            'beam_num': "0009",
            "energy": '6',
            'beam_type': 'HDTSE',
            'fff': '',
            'mvkv': '',
            'hdtse': 'HDTSE',
            'template': 'BeamCheckTemplate',
            'enhanced': ''
        },
    ),
    (
        "NDS-WKS-SN5432-2021-11-29-20-14-03-0014-BeamCheckTemplate2.5x",
        {
            'path': "NDS-WKS-SN5432-2021-11-29-20-14-03-0014-BeamCheckTemplate2.5x",
            'serial_no': '5432',
            'date': dt(2021, 11, 29, 20, 14, 3),
            'beam_num': "0014",
            "energy": '2.5',
            'beam_type': 'X',
            'fff': '',
            'mvkv': '',
            'hdtse': '',
            'template': 'BeamCheckTemplate',
            'enhanced': ''
        },
    ),


    # "Old" style
    (
        "NDS-WKS-SN4321-2015-12-03-15-45-31-0005-6eHDTSE-Beam",
        {
            'path': "NDS-WKS-SN4321-2015-12-03-15-45-31-0005-6eHDTSE-Beam",
            'serial_no': '4321',
            'date': dt(2015, 12, 3, 15, 45, 31),
            'beam_num': "0005",
            "energy": '6',
            'beam_type': 'HDTSE',
            'fff': '',
            'mvkv': '',
            'hdtse': 'HDTSE',
            'template': 'Beam',
            'enhanced': ''
        },
    ),
    (
        "NDS-WKS-SN4321-2019-02-12-20-42-27-0000-6xFFF-Beam",
        {
            'path': "NDS-WKS-SN4321-2019-02-12-20-42-27-0000-6xFFF-Beam",
            'serial_no': '4321',
            'date': dt(2019, 2, 12, 20, 42, 27),
            'beam_num': "0000",
            "energy": '6',
            'beam_type': 'FFF',
            'fff': 'FFF',
            'mvkv': '',
            'hdtse': '',
            'template': 'Beam',
            'enhanced': ''
        },
    ),
    (
        "NDS-WKS-SN4321-2019-02-12-20-42-27-0001-10x-Beam",
        {
            'path': "NDS-WKS-SN4321-2019-02-12-20-42-27-0001-10x-Beam",
            'serial_no': '4321',
            'date': dt(2019, 2, 12, 20, 42, 27),
            'beam_num': "0001",
            "energy": '10',
            'beam_type': 'X',
            'fff': '',
            'mvkv': '',
            'hdtse': '',
            'template': 'Beam',
            'enhanced': ''
        },
    ),
    (
        "NDS-WKS-SN4321-2019-02-12-20-42-27-0004-6e-Beam",
        {
            'path': "NDS-WKS-SN4321-2019-02-12-20-42-27-0004-6e-Beam",
            'serial_no': '4321',
            'date': dt(2019, 2, 12, 20, 42, 27),
            'beam_num': "0004",
            "energy": '6',
            'beam_type': 'E',
            'fff': '',
            'mvkv': '',
            'hdtse': '',
            'template': 'Beam',
            'enhanced': ''
        },
    ),
    (
        "NDS-WKS-SN4321-2019-02-12-20-42-28-0009-6x-Geometry",
        {
            'path': "NDS-WKS-SN4321-2019-02-12-20-42-28-0009-6x-Geometry",
            'serial_no': '4321',
            'date': dt(2019, 2, 12, 20, 42, 28),
            'beam_num': "0009",
            "energy": '6',
            'beam_type': 'X',
            'fff': '',
            'mvkv': '',
            'hdtse': '',
            'template': 'Geometry',
            'enhanced': ''
        },
    ),
]


@pytest.mark.parametrize("path,expected", dir_name_metas)
def test_mpc_path_to_meta(path, expected):
    assert mpc.mpc_path_to_meta(path) == expected


def test_group_by_metas():

    dir_names = [
        "NDS-WKS-SN5678-2020-06-25-07-11-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch",
        "NDS-WKS-SN5678-2020-06-25-07-12-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch",
        "NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
        "NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
        "NDS-WKS-SN1234-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-09-55-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-09-55-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-09-50-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-09-50-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-10-59-21-0009-GeometryCheckTemplate6xMVkV",
        "NDS-WKS-SN1234-2020-11-06-10-59-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-10-59-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-10-55-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-10-55-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-10-50-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-10-50-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN7890-2020-10-02-09-08-58-0009-BeamCheckTemplate6eHDTSE"
    ]

    expected_grouped = {
        "5678": {
            mpc.ENH_COUCH_CHECKS: {
                "2020-06-25-07-11": [
                    "NDS-WKS-SN5678-2020-06-25-07-11-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch"
                ],
                "2020-06-25-07-12": [
                    "NDS-WKS-SN5678-2020-06-25-07-12-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch"
                ],
            },
        },
        "6789": {
            mpc.ENH_MLC_CHECKS: {
                "2020-09-30-09-15": ["NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x"],
            },
        },
        "1234": {
            mpc.ENH_MLC_CHECKS: {
                "2020-09-30-09-15": [
                    "NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
                ],
            },
            mpc.ENH_COUCH_CHECKS: {
                "2020-10-01-11-26": [
                    "NDS-WKS-SN1234-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
                ],
            },
            mpc.BEAM_AND_GEOMETRY_CHECKS: {
                "2020-11-06-09-59": [
                    "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
                    "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
                    "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
                ],
                "2020-11-06-09-55": [
                    "NDS-WKS-SN1234-2020-11-06-09-55-21-0007-BeamCheckTemplate16e",
                    "NDS-WKS-SN1234-2020-11-06-09-55-21-0000-BeamCheckTemplate6xFFF",
                ],
                "2020-11-06-09-50": [
                    "NDS-WKS-SN1234-2020-11-06-09-50-21-0007-BeamCheckTemplate16e",
                    "NDS-WKS-SN1234-2020-11-06-09-50-21-0000-BeamCheckTemplate6xFFF",
                ],
                "2020-11-06-10-59": [
                    "NDS-WKS-SN1234-2020-11-06-10-59-21-0009-GeometryCheckTemplate6xMVkV",
                    "NDS-WKS-SN1234-2020-11-06-10-59-21-0007-BeamCheckTemplate16e",
                    "NDS-WKS-SN1234-2020-11-06-10-59-21-0000-BeamCheckTemplate6xFFF",
                ],
                "2020-11-06-10-55": [
                    "NDS-WKS-SN1234-2020-11-06-10-55-21-0007-BeamCheckTemplate16e",
                    "NDS-WKS-SN1234-2020-11-06-10-55-21-0000-BeamCheckTemplate6xFFF",
                ],
                "2020-11-06-10-50": [
                    "NDS-WKS-SN1234-2020-11-06-10-50-21-0007-BeamCheckTemplate16e",
                    "NDS-WKS-SN1234-2020-11-06-10-50-21-0000-BeamCheckTemplate6xFFF",
                ],
            }
        },
        "7890": {
            mpc.BEAM_AND_GEOMETRY_CHECKS: {
                "2020-10-02-09-08": ["NDS-WKS-SN7890-2020-10-02-09-08-58-0009-BeamCheckTemplate6eHDTSE"],
            },
        },
    }

    minutes = 3
    metas = [mpc.mpc_path_to_meta(f) for f in dir_names]
    grouped_metas = mpc.group_by_meta(metas, minutes)
    groups = {}
    for serial_no, template_type_metas in grouped_metas.items():
        groups[serial_no] = {}
        for template_type, date_metas in template_type_metas.items():
            groups[serial_no][template_type] = {date: [m['path'] for m in metas] for date, metas in date_metas.items()}

    assert groups == expected_grouped


def test_group_by_dates():

    dir_names = [
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-09-55-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-09-55-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-09-50-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-09-50-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-10-59-21-0009-GeometryCheckTemplate6xMVkV",
        "NDS-WKS-SN1234-2020-11-06-10-59-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-10-59-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-10-55-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-10-55-21-0000-BeamCheckTemplate6xFFF",
        "NDS-WKS-SN1234-2020-11-06-10-50-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN1234-2020-11-06-10-50-21-0000-BeamCheckTemplate6xFFF",
    ]

    grouped = {
        "2020-11-06-09-59": [
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
        ],
        "2020-11-06-09-55": [
            "NDS-WKS-SN1234-2020-11-06-09-55-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-55-21-0000-BeamCheckTemplate6xFFF",
        ],
        "2020-11-06-09-50": [
            "NDS-WKS-SN1234-2020-11-06-09-50-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-50-21-0000-BeamCheckTemplate6xFFF",
        ],
        "2020-11-06-10-59": [
            "NDS-WKS-SN1234-2020-11-06-10-59-21-0009-GeometryCheckTemplate6xMVkV",
            "NDS-WKS-SN1234-2020-11-06-10-59-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-10-59-21-0000-BeamCheckTemplate6xFFF",
        ],
        "2020-11-06-10-55": [
            "NDS-WKS-SN1234-2020-11-06-10-55-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-10-55-21-0000-BeamCheckTemplate6xFFF",
        ],
        "2020-11-06-10-50": [
            "NDS-WKS-SN1234-2020-11-06-10-50-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-10-50-21-0000-BeamCheckTemplate6xFFF",
        ],
    }

    minutes = 3
    metas = [mpc.mpc_path_to_meta(f) for f in dir_names]
    groups = {date: [m['path'] for m in metas] for date, metas in mpc.group_by_dates(metas, minutes).items()}
    assert groups == grouped


def test_group_by_sn():

    dir_names = [
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
        "NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
        "NDS-WKS-SN4567-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
        "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
    ]

    metas = [mpc.mpc_path_to_meta(f) for f in dir_names]
    groups = {sn: [m['path'] for m in metas] for sn, metas in mpc.group_by_sn(metas).items()}

    expected = {
        "1234": [
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
        ],
        "4567": [
            "NDS-WKS-SN4567-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
        ],
        "6789": [
            "NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
        ],
    }

    assert groups == expected


now = dt.now()
@pytest.mark.parametrize("ts,cutoff,expected", [  # noqa: E302
    (now.timestamp(), now + timedelta(hours=1), False),
    (now.timestamp(), now - timedelta(hours=1), True),
    (now.timestamp(), now, False),
])
def test_timestamp_filter(ts, cutoff, expected):
    assert mpc.timestamp_filter(ts, cutoff) == expected


class TestQATrackMPCPump:

    def setup_class(self):
        self.app = wx.App()
        self.pump = mpc.QATrackMPCPump()
        self.pump.log = mock.Mock()

    @pytest.mark.parametrize("tds,valid_expected,msg_expected", [
        ("", False, "set a source"),
        ("/does/not/exist", False, "not a valid directory"),
        (1, False, "not a valid file path"),
        (".", True, "OK"),
    ])
    def test_validate_mpc(self, tds, valid_expected, msg_expected):
        valid, msg = self.pump.validate_mpc({'tds directory': tds})
        assert valid is valid_expected
        assert msg_expected in msg

    @pytest.mark.parametrize("name,valid_expected,msg_expected", [
        ("", False, "must include"),
        ("Foo {{ bar }} baz qux", False, "must include"),
        ("Foo {{ check_type } baz qux", False, "must include"),
        ("Foo {{ check_type }} bar", True, "OK"),
    ])
    def test_validate_test_list(self, name, valid_expected, msg_expected):
        valid, msg = self.pump.validate_test_list({'name': name})
        assert valid is valid_expected
        assert msg_expected in msg

    def test_caches_cleared_before_pump(self):

        self.pump._unit_cache = {'not empty': 123}
        self.pump._record_meta_cache = {'not empty': 123}
        with mock.patch("qcpump.pumps.common.qatrack.QATrackFetchAndPost.pump"):
            with mock.patch("qcpump.contrib.pumps.mpc.mpc.QATrackMPCPump.set_qatrack_unit_names_to_ids"):
                self.pump.pump()
                assert not self.pump._record_meta_cache
                assert not self.pump._unit_cache

    def test_history_cutoff_date(self):

        self.pump.state = {
            "MPC": {'subsections': [[{'config_name': 'history days', 'value': 1}]]}
        }
        expected = dt.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        assert self.pump.history_cutoff_date() == expected

    def test_group_records(self):
        dir_names = [
            "NDS-WKS-SN5678-2020-06-25-07-11-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch",
            "NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
            "NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x",
            "NDS-WKS-SN1234-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
            "NDS-WKS-SN1234-2020-11-06-09-55-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-55-21-0000-BeamCheckTemplate6xFFF",
            "NDS-WKS-SN1234-2020-11-06-09-50-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-09-50-21-0000-BeamCheckTemplate6xFFF",
            "NDS-WKS-SN1234-2020-11-06-10-59-21-0009-GeometryCheckTemplate6xMVkV",
            "NDS-WKS-SN1234-2020-11-06-10-59-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-10-59-21-0000-BeamCheckTemplate6xFFF",
            "NDS-WKS-SN1234-2020-11-06-10-55-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-10-55-21-0000-BeamCheckTemplate6xFFF",
            "NDS-WKS-SN1234-2020-11-06-10-50-21-0007-BeamCheckTemplate16e",
            "NDS-WKS-SN1234-2020-11-06-10-50-21-0000-BeamCheckTemplate6xFFF",
        ]

        expected_grouped = [
            ("5678", mpc.ENH_COUCH_CHECKS, "2020-06-25-07-11", [
                "NDS-WKS-SN5678-2020-06-25-07-11-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch"
            ]),
            ("6789", mpc.ENH_MLC_CHECKS, "2020-09-30-09-15", [
                "NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x"
            ]),
            ("1234", mpc.ENH_MLC_CHECKS, "2020-09-30-09-15", [
                "NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x"
            ]),
            ("1234", mpc.ENH_COUCH_CHECKS, "2020-10-01-11-26", [
                "NDS-WKS-SN1234-2020-10-01-11-26-55-0010-GeometryCheckTemplate6xMVkVEnhancedCouch"
            ]),
            ("1234", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-11-06-09-50", [
                "NDS-WKS-SN1234-2020-11-06-09-50-21-0007-BeamCheckTemplate16e",
                "NDS-WKS-SN1234-2020-11-06-09-50-21-0000-BeamCheckTemplate6xFFF",
            ]),
            ("1234", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-11-06-09-55", [
                "NDS-WKS-SN1234-2020-11-06-09-55-21-0007-BeamCheckTemplate16e",
                "NDS-WKS-SN1234-2020-11-06-09-55-21-0000-BeamCheckTemplate6xFFF",
            ]),
            ("1234", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-11-06-09-59", [
                "NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV",
                "NDS-WKS-SN1234-2020-11-06-09-59-21-0007-BeamCheckTemplate16e",
                "NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF",
            ]),
            ("1234", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-11-06-10-50", [
                "NDS-WKS-SN1234-2020-11-06-10-50-21-0007-BeamCheckTemplate16e",
                "NDS-WKS-SN1234-2020-11-06-10-50-21-0000-BeamCheckTemplate6xFFF",
            ]),
            ("1234", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-11-06-10-55", [
                "NDS-WKS-SN1234-2020-11-06-10-55-21-0007-BeamCheckTemplate16e",
                "NDS-WKS-SN1234-2020-11-06-10-55-21-0000-BeamCheckTemplate6xFFF",
            ]),
            ("1234", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-11-06-10-59", [
                "NDS-WKS-SN1234-2020-11-06-10-59-21-0009-GeometryCheckTemplate6xMVkV",
                "NDS-WKS-SN1234-2020-11-06-10-59-21-0007-BeamCheckTemplate16e",
                "NDS-WKS-SN1234-2020-11-06-10-59-21-0000-BeamCheckTemplate6xFFF",
            ]),
        ]
        expected_grouped_with_meta = []
        for sn, template, date, paths in expected_grouped:
            expected_grouped_with_meta.append((sn, template, date, list([mpc.mpc_path_to_meta(p) for p in paths])))

        self.pump.state = {
            "MPC": {'subsections': [[{'config_name': 'grouping window', 'value': 3}]]}
        }
        assert self.pump.group_records(dir_names) == expected_grouped_with_meta

    def test_filter_records(self):

        records = [
            ("5678", mpc.ENH_COUCH_CHECKS, "2020-06-25-07-11", [
                mpc.mpc_path_to_meta("NDS-WKS-SN5678-2020-06-25-07-11-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch")]),  # noqa: E501
            ("6789", mpc.ENH_MLC_CHECKS, "2020-09-30-09-15", [
                mpc.mpc_path_to_meta("NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x")]),
            ("1234", mpc.ENH_MLC_CHECKS, "2020-09-30-09-15", [
                mpc.mpc_path_to_meta("NDS-WKS-SN1234-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x")]),
        ]

        cutoff = (dt.now() - dt(2020, 7, 1)).days*24*60
        self.pump.state = {
            "MPC": {'subsections': [[{'config_name': 'wait time', 'value': cutoff}]]}
        }
        assert self.pump.filter_records(records) == records[:1]

    def test_id_for_record(self):
        record = ("5678", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-06-25-07-11", [])
        assert self.pump.id_for_record(record) == f"QCPump/MPC/5678/2020-06-25-07-11/{mpc.BEAM_AND_GEOMETRY_CHECKS}"

    @pytest.mark.parametrize("record,expected", [
        (("5678", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-06-25-07-11", []), "MPC: Beam and Geometry Checks"),
        (("5678", mpc.ENH_MLC_CHECKS, "2020-06-25-07-11", []), "MPC: Enhanced MLC Checks"),
        (("5678", mpc.ENH_COUCH_CHECKS, "2020-06-25-07-11", []), "MPC: Enhanced Couch Checks"),
    ])
    def test_test_list_for_record(self, record, expected):
        self.pump.state = {
            "Test List": {'subsections': [[{'config_name': 'name', 'value': "MPC: {{ check_type }}"}]]}
        }
        assert self.pump.test_list_for_record(record) == expected

    def test_qatrack_unit_for_record(self):
        units = [{'serial_number': '5678', 'name': "Unit5678"}]
        with mock.patch.object(self.pump, "get_qatrack_choices", return_value=units):
            with mock.patch.object(self.pump, 'construct_api_url'):
                self.pump.qatrack_unit_for_record(("5678", "", "", [])) == "Unit5678"

    def test_qatrack_unit_for_record_not_found(self):
        units = [{'serial_number': '5678', 'name': "Unit5678"}]
        with mock.patch.object(self.pump, "get_qatrack_choices", return_value=units):
            with mock.patch.object(self.pump, 'construct_api_url'):
                self.pump.qatrack_unit_for_record(("1234", "", "", [])) is None

    def test_values_from_record(self):
        rows = io.StringIO("""Name [Unit],Value,Threshold,Evaluation Result
CollimationGroup/MLCGroup/MLCMaxOffsetA [mm],0.4,1,Pass
CollimationGroup/MLCGroup/MLCMaxOffsetB [mm],0.43,1,Pass
CollimationGroup/MLCGroup/MLCMeanOffsetA [mm],0.3,1,Pass
CollimationGroup/MLCGroup/MLCMeanOffsetB [mm],0.27,1,Pass
CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf1 [mm],0.27,1,Pass
CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf2 [mm],0.34,1,Pass
CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf3 [mm],0.3,1,Pass
CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf4 [mm],0.23,1,Pass
""")
        path_mock = mock.MagicMock()
        path_mock.open.return_value = rows
        meta = {
            'path': path_mock,
            'energy': '6',
            'beam_type': 'X',
        }

        record = ("5678", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-06-25-07-11", [meta])

        res = self.pump.test_values_from_record(record)
        expected = {
            'collimationgroup_mlcgroup_mlcmaxoffseta_mm_6x': {
                'value': 0.4,
                'comment': 'Threshold: 1.000,Result: Pass',
            },
            'collimationgroup_mlcgroup_mlcmaxoffsetb_mm_6x': {
                'value': 0.43,
                'comment': 'Threshold: 1.000,Result: Pass',
            },
            'collimationgroup_mlcgroup_mlcmeanoffseta_mm_6x': {
                'value': 0.3,
                'comment': 'Threshold: 1.000,Result: Pass',
            },
            'collimationgroup_mlcgroup_mlcmeanoffsetb_mm_6x': {
                'value': 0.27,
                'comment': 'Threshold: 1.000,Result: Pass',
            },
        }
        assert res == expected

    def test_fetch_records(self):
        """This test is weak :p"""

        self.pump.state = {
            "MPC": {
                'subsections': [[
                    {'config_name': 'tds directory', 'value': "."},
                    {'config_name': 'history days', 'value': 1},
                    {'config_name': 'wait time', 'value': 1},
                ]],
            }
        }
        assert self.pump.fetch_records() == []

    def test_comment_for_record(self):
        res = self.pump.comment_for_record(("123", "", "", [{'path': r"I:\Foo\Bar"}]))
        assert res == "Fileset:\n\tI:\\Foo\\Bar"

    def test_autoskip(self):
        assert self.pump.autoskip

    meta1 = {'date': dt(2020, 6, 25, 7, 11)}
    meta2 = {'date': dt(2020, 6, 25, 7, 13)}
    @pytest.mark.parametrize("metas,ws,wc", [  # noqa: E301
        ([meta1, meta2], meta1['date'], meta2['date']),
        ([meta2, meta1], meta1['date'], meta2['date']),
        ([meta1, meta1], meta1['date'], meta1['date'] + timedelta(minutes=1)),
    ])
    def test_work_datetimes_for_record(self, metas, ws, wc):
        record = ("5678", mpc.BEAM_AND_GEOMETRY_CHECKS, "2020-06-25-07-11", metas)
        res = self.pump.work_datetimes_for_record(record)
        assert res == (ws, wc)
