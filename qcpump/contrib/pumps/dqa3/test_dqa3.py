from collections import defaultdict
import datetime
from unittest import mock

import pytest
import wx

from qcpump.contrib.pumps.dqa3 import dqa3pump

dt1 = datetime.datetime(2021, 3, 31, 1, 23)
dt2 = datetime.datetime(2021, 3, 31, 1, 24)


class TestDQA3:

    def setup_class(self):
        self.app = wx.App()

    def get_pump(self, klass):
        pump = klass()
        pump.log = mock.Mock()
        return pump

    @pytest.mark.parametrize("klass,driver,querier", [
        (dqa3pump.AtlasDQA3, "mssql", dqa3pump.mssql_query),
        (dqa3pump.FirebirdDQA3, "fdb", dqa3pump.fdb_query),
        (dqa3pump.FirebirdDQA3, "firebirdsql", dqa3pump.firebirdsql_query),
    ])
    def test_mssql_querier(self, klass, driver, querier):
        dqa3 = self.get_pump(klass)
        dqa3.get_config_value = mock.Mock(return_value=driver)
        assert dqa3.querier == querier

    @pytest.mark.parametrize("name,valid_expected,msg_expected", [
        ("", False, "must include"),
        ("Foo {{ beam_type }} baz qux", False, "must include"),
        ("Foo {{ energy } baz qux", False, "must include"),
        ("Foo {{ beam_type }} {{ energy}}bar", True, "OK"),
    ])
    def test_validate_test_list(self, name, valid_expected, msg_expected):
        pump = dqa3pump.BaseDQA3()
        valid, msg = pump.validate_test_list({'name': name})
        assert valid is valid_expected
        assert msg_expected in msg

    @pytest.mark.parametrize("prop,prop_val,valid_expected,msg_expected", [
        ("host", "", False, "set a value for the host setting"),
        ("port", "", False, "set a value for the port setting"),
        ("user", "", False, "set both the user and password"),
        ("database", "", False, "set the name of the database"),
    ])
    def test_validate_dqa3reader_no_host(self, prop, prop_val, valid_expected, msg_expected):
        props = defaultdict(lambda: "")
        props[prop] = prop_val
        valid, msg = dqa3pump.BaseDQA3().validate_dqa3reader(props)
        assert valid is valid_expected
        assert msg_expected in msg

    @pytest.mark.parametrize("version,expected_valid,expected_msg", [
        ("1.5", True, "Successful connection"),
        ("9.9", False, "Unknown database type"),
    ])
    def test_validate_dqa3reaer_dqa3_connect(self, version, expected_valid, expected_msg):
        props = {
            'host': 'host',
            'port': 'port',
            'user': 'user',
            'password': 'password',
            'database': 'database'
        }
        pump = self.get_pump(dqa3pump.AtlasDQA3)

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", return_value=[(version,)]):
            with mock.patch.object(pump, "db_connect_kwargs"):
                valid, msg = pump.validate_dqa3reader(props)
                assert valid is expected_valid
                assert expected_msg in msg

    def test_validate_dqa3reaer_dqa3_connect_failure(self):
        props = {
            'host': 'host',
            'port': 'port',
            'user': 'user',
            'password': 'password',
            'database': 'database'
        }
        pump = self.get_pump(dqa3pump.AtlasDQA3)

        def fail(*args):
            raise Exception("some failure")

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", side_effect=fail):
            with mock.patch.object(pump, "db_connect_kwargs"):
                valid, msg = pump.validate_dqa3reader(props)
                assert not valid
                assert "some failure" in msg

    @pytest.mark.parametrize("values,valid_expected,msg_expected", [
        ({'dqa3 name': 'ok', 'unit name': ''}, False, "Please complete both"),
        ({'dqa3 name': '', 'unit name': 'ok'}, False, "Please complete both"),
        ({'dqa3 name': 'ok', 'unit name': 'ok'}, True, "OK"),
    ])
    def test_validate_units(self, values, valid_expected, msg_expected):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        valid, msg = pump.validate_units(values)
        assert valid is valid_expected
        assert msg_expected in msg

    def test_db_connect_kwargs(self):
        props = [{
            'host': 'host',
            'port': 'port',
            'user': 'user',
            'password': 'password',
            'database': 'database',
            'driver': 'fdb',
        }]
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        with mock.patch.object(pump, "get_config_values", return_value=props):
            ret = pump.db_connect_kwargs()
            assert ret == props[0]

    def test_get_dqa3_unit_choices_no_db(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        assert pump.get_dqa3_unit_choices() == []

    def test_get_dqa3_unit_choices(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        pump.db_version = "1.5"

        return_val = [
            {'machine_id': 1, 'machine_name': 'Unit 1', 'room_name': "Room 1"},
            {'machine_id': 2, 'machine_name': 'Unit 2', 'room_name': "Room 2"},
            {'machine_id': 3, 'machine_name': 'Unit 3', 'room_name': None},
        ]

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", return_value=return_val):
            with mock.patch.object(pump, "db_connect_kwargs"):
                expected = ["Room 1/Unit 1", "Room 2/Unit 2", "Unit 3"]
                assert pump.get_dqa3_unit_choices() == expected

    def test_get_dqa3_unit_choices_fail(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        pump.db_version = "1.5"

        def fail(*args, **kwargs):
            raise Exception("some failure")

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", side_effect=fail):
            with mock.patch.object(pump, "db_connect_kwargs"):
                pump.get_dqa3_unit_choices()
                assert "Querying units resulted in an error" in pump.log.call_args[0][1]

    def test_id_for_record(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        dt = datetime.datetime(2021, 3, 31, 1, 23, 34)
        rec = {'data_key': 'foo', 'machine_id': 1, 'machine_name': "Unit 1", "room_name": None, 'work_started': dt, 'wedge_type': 'EDW', 'wedge_angle': "60", 'wedge_orient': 'Bottom-Top'}
        assert pump.id_for_record(rec) == "QCPump/DQA3/1/2021-03-31 01:23:34/foo"

    def test_qatrack_unit_for_record(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        pump.dqa_machine_name_to_id['dqa3unitname'] = 1
        config = [{'dqa3 name': 'dqa3unitname', 'unit name': 'qatrackunitname'}]
        with mock.patch.object(pump, "get_config_values", return_value=config):
            assert pump.qatrack_unit_for_record({'machine_id': 1}) == 'qatrackunitname'

    def test_work_datetimes(self):
        dt1 = datetime.datetime.now()
        dt2 = dt1 + datetime.timedelta(minutes=1)
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        assert pump.work_datetimes_for_record({'work_started': dt1, 'work_completed': dt2}) == (dt1, dt2)

    def test_values_from_record(self):
        record = {
            'work_completed': -1,
            'work_started': -1,
            'comment': -1,
            'machine_id': -1,
            'beam_energy': -1,
            'beam_type': -1,
            'test1': 1,
            'test2': 2,
        }
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        assert pump.test_values_from_record(record) == {'test1': {'value': 1}, 'test2': {'value': 2}}

    @pytest.mark.parametrize("comment,expected", [
        ("", ""),
        (None, ""),
        ("comment", "comment")
    ])
    def test_comment_for_record(self, comment, expected):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        assert pump.comment_for_record({'comment': comment}) == expected

    def test_history_days(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        with mock.patch.object(pump, "get_config_value", return_value=123):
            assert pump.history_days == 123

    def test_min_date(self):
        now = datetime.datetime.now().date()
        expected = now - datetime.timedelta(days=3)
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        with mock.patch.object(pump, "get_config_value", return_value=3):
            assert pump.min_date == expected

    def test_fetch_records(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)

        with mock.patch.object(pump, "prepare_dqa3_query", return_value=["", []]):
            with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", return_value=[{'some': 'results'}]):
                with mock.patch.object(pump, "db_connect_kwargs"):
                    records = pump.fetch_records()
                    assert records == [{'some': 'results'}]

    def test_fetch_records_fails(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)

        def fail(*args):
            raise Exception("some failure")

        with mock.patch.object(pump, "prepare_dqa3_query", side_effect=fail):
            assert pump.fetch_records() == []

    def test_prepare_dqa3_query_mssql(self):

        now = datetime.datetime.now()
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        trend_query_path = pump.get_pump_path() / "queries" / "mssql" / "1.5" / "trend.sql"
        pump.dqa3_trend_query = trend_query_path.read_text()
        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.unit_map", new_callable=mock.PropertyMock) as mock_unit_map:  # noqa: E501
            mock_unit_map.return_value = {'dqa unit 1': 'unit 1', 'dqa unit 2': 'unit 2'}
            with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.min_date", new_callable=mock.PropertyMock) as mock_min_date:  # noqa: E501
                mock_min_date.return_value = now
                q, params = pump.prepare_dqa3_query()
                assert "data.created >= ?" in q
                assert "mach.MachineId IN (?,?)" in q
                assert params == [now, "dqa unit 1", "dqa unit 2"]

    @pytest.mark.parametrize("record,expected", [
        ({"beam_type": "FfF", "beam_energy": 6, 'wedge_type': "", "wedge_angle": "", 'wedge_orient': "", "device": "", "machine_name": "", "room_name": "", "beam_name": ""}, "DQA3: 6FFF"),
        ({"beam_type": "eLecTron", "beam_energy": 6, 'wedge_type': "", "wedge_angle": "", 'wedge_orient': "", "device": "", "machine_name": "", "room_name": "", "beam_name": ""}, "DQA3: 6E"),
        ({"beam_type": "PhOtOn", "beam_energy": 6, 'wedge_type': "", "wedge_angle": "", 'wedge_orient': "", "device": "", "machine_name": "", "room_name": "", "beam_name": ""}, "DQA3: 6X"),
        ({"beam_type": "PhOtOn", "beam_energy": 6, 'wedge_type': "EDW", "wedge_angle": "60", 'wedge_orient': "", "device": "", "machine_name": "", "room_name": "", "beam_name": ""}, "DQA3: 6XEDW60"),
    ])
    def test_test_list_for_record(self, record, expected):

        pump = self.get_pump(dqa3pump.AtlasDQA3)
        with mock.patch.object(pump, "get_config_value", return_value="DQA3: {{energy}}{{beam_type}}{{wedge_type}}{{wedge_angle}}"):
            assert pump.test_list_for_record(record) == expected


class TestDQA3Grouped:

    def setup_class(self):
        self.app = wx.App()

    def get_pump(self, klass):
        pump = klass()
        pump.log = mock.Mock()
        return pump

    def test_group_by_machine_date(self):
        dt1 = datetime.datetime(2021, 3, 31, 1, 23, 34)
        dt2 = dt1 + datetime.timedelta(minutes=1)
        dt3 = dt2 + datetime.timedelta(minutes=1)
        dt4 = dt3 + datetime.timedelta(minutes=10)
        dt5 = dt4 + datetime.timedelta(minutes=1)

        rows = [
            {'data_key': 1, 'machine_id': 1, 'work_started': dt1},
            {'data_key': 2, 'machine_id': 2, 'work_started': dt1},
            {'data_key': 3, 'machine_id': 1, 'work_started': dt2},
            {'data_key': 4, 'machine_id': 2, 'work_started': dt2},
            {'data_key': 5, 'machine_id': 1, 'work_started': dt3},
            {'data_key': 6, 'machine_id': 2, 'work_started': dt3},

            {'data_key': 7, 'machine_id': 1, 'work_started': dt4},
            {'data_key': 8, 'machine_id': 2, 'work_started': dt4},
            {'data_key': 9, 'machine_id': 1, 'work_started': dt5},
            {'data_key': 0, 'machine_id': 2, 'work_started': dt5},
        ]

        res = dqa3pump.group_by_machine_dates(rows, 3)

        expected = {
            1: {
                "2021-03-31-01-23": [
                    {"data_key": 1, "machine_id": 1, "work_started": dt1},
                    {"data_key": 3, "machine_id": 1, "work_started": dt2},
                    {"data_key": 5, "machine_id": 1, "work_started": dt3}
                ],
                "2021-03-31-01-35": [
                    {"data_key": 7, "machine_id": 1, "work_started": dt4},
                    {"data_key": 9, "machine_id": 1, "work_started": dt5}
                ]
            },
            2: {
                "2021-03-31-01-23": [
                    {"data_key": 2, "machine_id": 2, "work_started": dt1},
                    {"data_key": 4, "machine_id": 2, "work_started": dt2},
                    {"data_key": 6, "machine_id": 2, "work_started": dt3}
                ],
                "2021-03-31-01-35": [
                    {"data_key": 8, "machine_id": 2, "work_started": dt4},
                    {"data_key": 0, "machine_id": 2, "work_started": dt5}
                ]
            }
        }
        assert res == expected

    @pytest.mark.parametrize("name,valid_expected,msg_expected", [
        ("", False, "You must set a test list name"),
        ("DQA3 Results", True, "OK"),
    ])
    def test_validate_test_list(self, name, valid_expected, msg_expected):
        pump = dqa3pump.BaseGroupedDQA3()
        valid, msg = pump.validate_test_list({'name': name})
        assert valid is valid_expected
        assert msg_expected in msg

    def test_fetch_records(self):
        pump = self.get_pump(dqa3pump.AtlasGroupedDQA3)

        pump.state = {
            "DQA3Reader": {
                'subsections': [[
                    {'config_name': 'history days', 'value': 1},
                    {'config_name': 'wait time', 'value': 1},
                    {'config_name': 'grouping window', 'value': 1},
                ]],
            }
        }
        dt1 = datetime.datetime(2021, 3, 31, 1, 23, 34)
        fetch_results = [{'data_key': 1, 'machine_id': 1, 'work_started': dt1}]
        results = [
            (1, '2021-03-31-01-23', fetch_results),
        ]
        with mock.patch.object(pump, "prepare_dqa3_query", return_value=["", []]):
            with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", return_value=fetch_results):
                with mock.patch.object(pump, "db_connect_kwargs"):
                    records = pump.fetch_records()
                    assert records == results

    def test_id_for_record(self):
        pump = self.get_pump(dqa3pump.AtlasGroupedDQA3)
        dt1 = datetime.datetime(2021, 3, 31, 1, 23, 34)
        fetch_results = [
            {'data_key': 123, 'machine_id': 1, 'work_started': dt1},
            {'data_key': 456, 'machine_id': 1, 'work_started': dt1},
        ]
        rec = (1, '2021-03-31-01-23', fetch_results)
        assert pump.id_for_record(rec) == "QCPump/DQA3/1/2021-03-31-01-23/123/456"

    def test_values_from_record(self):

        dt1 = datetime.datetime(2021, 3, 31, 1, 23)
        dt2 = datetime.datetime(2021, 3, 31, 1, 24)
        fetch_results = [
                {'machine_id': 1, 'data_key': 1, 'work_started': dt1, 'comment': 'comment 1', 'machine_name': 'machine1', 'room_name': '', 'signature': 'username', 'device': '1234567', 'beam_energy': 6, 'beam_type': 'Photon', 'temperature': 21.8, 'pressure': 104.6, 'dose': 99.05, 'dose_baseline': 100.000, 'dose_diff': -0.95, 'wedge_type': 'EDW', 'wedge_angle': "60", 'wedge_orient': 'Bottom-Top', 'beam_name': "foo"},
                {'machine_id': 1, 'data_key': 1, 'work_started': dt2, 'comment': 'comment 1', 'machine_name': 'machine1', 'room_name': '', 'signature': 'username', 'device': '1234567', 'beam_energy': 9, 'beam_type': 'Electron', 'temperature': 21.8, 'pressure': 104.6, 'dose': 99.05, 'dose_baseline': 100.000, 'dose_diff': -0.95, 'wedge_type': '', 'wedge_angle': "", 'wedge_orient': '', 'beam_name': "foo"},
        ]

        rec = (1, '2021-03-31-01-23', fetch_results)
        pump = self.get_pump(dqa3pump.AtlasGroupedDQA3)
        results = pump.test_values_from_record(rec)
        expected = {
            'data_key_6xedw60': {'value': 1},
            'data_key_9e': {'value': 1},
            'device_6xedw60': {'value': '1234567'},
            'device_9e': {'value': '1234567'},
            'dose_6xedw60': {'value': 99.05},
            'dose_9e': {'value': 99.05},
            'dose_baseline_6xedw60': {'value': 100.0},
            'dose_baseline_9e': {'value': 100.0},
            'dose_diff_6xedw60': {'value': -0.95},
            'dose_diff_9e': {'value': -0.95},
            'machine_name_6xedw60': {'value': 'machine1'},
            'machine_name_9e': {'value': 'machine1'},
            'pressure_6xedw60': {'value': 104.6},
            'pressure_9e': {'value': 104.6},
            'room_name_6xedw60': {'value': ''},
            'room_name_9e': {'value': ''},
            'signature_6xedw60': {'value': 'username'},
            'signature_9e': {'value': 'username'},
            'temperature_6xedw60': {'value': 21.8},
            'temperature_9e': {'value': 21.8}
        }
        assert results == expected

    @pytest.mark.parametrize("method,expected",[
        ("work_datetimes_for_record", (dt1, dt2)),
        ("comment_for_record", "comment 1\ncomment 2"),
        ("test_list_for_record", "DQA3 Results"),
        ("qatrack_unit_for_record", "qatrackunitname"),
    ])
    def test_record_meta(self, method, expected):
        fetch_results = [
                {'machine_id': 1, 'data_key': 1, 'work_started': dt2, 'comment': 'comment 1', 'machine_name': 'machine1', 'room_name': '', 'signature': 'username', 'device': '1234567', 'beam_energy': 6, 'beam_type': 'Electron', 'wedge_type': 'EDW', 'wedge_angle': "60", 'wedge_orient': 'Bottom-Top', 'temperature': 21.8, 'pressure': 104.6, 'dose': 99.05, 'dose_baseline': 100.000, 'dose_diff': -0.95},
                {'machine_id': 1, 'data_key': 1, 'work_started': dt1, 'comment': 'comment 2', 'machine_name': 'machine1', 'room_name': '', 'signature': 'username', 'device': '1234567', 'beam_energy': 9, 'beam_type': 'Electron', 'wedge_type': 'EDW', 'wedge_angle': "60", 'wedge_orient': 'Bottom-Top', 'temperature': 21.8, 'pressure': 104.6, 'dose': 99.05, 'dose_baseline': 100.000, 'dose_diff': -0.95},
        ]

        rec = (1, '2021-03-31-01-23', fetch_results)
        pump = self.get_pump(dqa3pump.AtlasGroupedDQA3)
        pump.dqa_machine_name_to_id['dqa3unitname'] = 1

        pump.state = {
            "Test List": {
                'subsections': [[
                    {'config_name': 'name', 'value': "DQA3 Results"},
                ]],
            }
        }
        config = [{'dqa3 name': 'dqa3unitname', 'unit name': 'qatrackunitname'}]
        with mock.patch.object(pump, "get_config_values", return_value=config):
            results = getattr(pump, method)(rec)
            assert results == expected
