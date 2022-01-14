import pytest

from qcpump.pumps.common.qatrack import slugify


@pytest.mark.parametrize("value,expected", [
    ("6 MV  -", "_6_mv"),
    ("Flatness 6 MV", "flatness_6_mv"),
    ("Flatness 6MV [%]", "flatness_6mv_per"),
    ("X Width 6MV [mm]", "x_width_6mv_mm"),
    ("2.5X", "2_5X"),
])
def test_slugify(value, expected):
    assert slugify(value) == expected
