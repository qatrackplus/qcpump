from collections import defaultdict
import datetime
from unittest import mock

import pytest
import wx

from qcpump.contrib.pumps.dqa3 import dqa3pump


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

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", return_value=[("Unit 2",), ("Unit 1",)]):
            with mock.patch.object(pump, "db_connect_kwargs"):
                assert pump.get_dqa3_unit_choices() == ["Unit 1", "Unit 2"]

    def test_get_dqa3_unit_choices_fail(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        pump.db_version = "1.5"

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", return_value=[("Unit 2",), ("Unit 1",)]):
            with mock.patch.object(pump, "db_connect_kwargs"):
                assert pump.get_dqa3_unit_choices() == ["Unit 1", "Unit 2"]

        def fail(*args):
            raise Exception("some failure")

        with mock.patch("qcpump.contrib.pumps.dqa3.dqa3pump.BaseDQA3.querier", side_effect=fail):
            with mock.patch.object(pump, "db_connect_kwargs"):
                pump.get_dqa3_unit_choices()
                assert "Querying units resulted in an error" in pump.log.call_args[0][1]

    def test_id_for_record(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        assert pump.id_for_record({'data_key': 'foo'}) == "QCPump::DQA3::foo"

    def test_qatrack_unit_for_record(self):
        pump = self.get_pump(dqa3pump.AtlasDQA3)
        config = [{'dqa3 name': 'dqa3unitname', 'unit name': 'qatrackunitname'}]
        with mock.patch.object(pump, "get_config_values", return_value=config):
            assert pump.qatrack_unit_for_record({'dqa3_unit_name': 'dqa3unitname'}) == 'qatrackunitname'

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
            'dqa3_unit_name': -1,
            'beamenergy': -1,
            'beamtype': -1,
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
                assert "mach.MachineName IN (?,?)" in q
                assert params == [now, "dqa unit 1", "dqa unit 2"]

    @pytest.mark.parametrize("record,expected", [
        ({"beamtype": "FfF", "beamenergy": 6}, "DQA3: 6FFF"),
        ({"beamtype": "eLecTron", "beamenergy": 6}, "DQA3: 6E"),
        ({"beamtype": "PhOtOn", "beamenergy": 6}, "DQA3: 6X"),
    ])
    def test_test_list_for_record(self, record, expected):

        pump = self.get_pump(dqa3pump.AtlasDQA3)
        with mock.patch.object(pump, "get_config_value", return_value="DQA3: {{energy}}{{beam_type}}"):
            assert pump.test_list_for_record(record) == expected
