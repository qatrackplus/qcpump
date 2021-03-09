import pytest

from qcpump.pumps import dependencies


@pytest.fixture
def section_dependencies():
    return {
        'dqa3': [],
        'qatrack': [],
        'test list': ['qatrack'],
        'unit': ['dqa3', 'qatrack'],
        'level2': ['dqa3'],
        'level3': ['unit', 'qatrack'],
    }


def test_generate_validation_levels(section_dependencies):
    levels = dependencies.generate_validation_levels(section_dependencies)
    expected = [
        {'dqa3', 'qatrack'},
        {'test list', 'unit', 'level2'},
        {'level3'},
    ]
    assert levels == expected


@pytest.mark.parametrize(
    "section,expected", [
        ('dqa3', [{'dqa3'}, {'level2', 'unit'}, {'level3'}]),
        ('qatrack', [{'qatrack'}, {'test list', 'unit'}, {'level3'}]),
        ('test list', [{'test list'}]),
        ('unit', [{'unit'}, {'level3'}]),
        ('level2', [{'level2'}]),
        ('level3', [{'level3'}]),
    ]
)
def test_generate_validation_level_subset(section_dependencies, section, expected):
    assert dependencies.generate_validation_level_subset(section, section_dependencies) == expected


def test_generate_validation_level_subset_doc_example():
    deps = {
        'a': [],
        'b': ['a'],
        'c': [],
        'd': ['b', 'c'],
    }
    section = 'b'
    assert dependencies.generate_validation_level_subset(section, deps) == [{'b'}, {'d'}]


def test_depends_directl_on():
    deps = {
        'a': [],
        'b': ['a'],
        'c': [],
        'd': ['b', 'c'],
    }
    expected = {
        'a': set('b'),
        'b': set('d'),
        'c': set('d'),
        'd': set(),
    }
    assert dependencies.depends_directly_on(deps) == expected
