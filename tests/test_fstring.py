# -*- coding=utf-8 -*-
from string import Formatter

import pytest

from pyoptimizer.optimizations.fstring import Format, parse_old_format

test_regex_data = [
    pytest.param("%(a)s, %(b)s", [
        Format(literal_text="", field_name="a", format_spec="s"),
        Format(literal_text=", ", field_name="b", format_spec="s")
    ]),
    pytest.param("%(Dating)s, %(Income)2.2f", [
        Format(literal_text="", field_name="Dating", format_spec="s"),
        Format(literal_text=", ", field_name="Income", format_spec="2.2f")
    ]),
    pytest.param("%s %d", [
        Format(literal_text="", field_name="", format_spec="s"),
        Format(literal_text=" ", field_name="", format_spec="d")
    ]),

    pytest.param("xxx%d", [
        Format(literal_text="xxx", field_name="", format_spec="d"),
    ], id="proceeding"),
    pytest.param("%dxxx", [
        Format(literal_text="", field_name="", format_spec="d"),
        Format(literal_text="xxx", field_name=None, format_spec=None)
    ], id="trailing"),

    pytest.param("%%", [
        Format(literal_text="%", field_name=None, format_spec=None)
    ], id="%"),
    pytest.param("%%%%", [
        Format(literal_text="%", field_name=None, format_spec=None),
        Format(literal_text="%", field_name=None, format_spec=None),
    ], id="%%"),
    pytest.param("%%%x", [
        Format(literal_text="%", field_name=None, format_spec=None),
        Format(literal_text="", field_name="", format_spec="x"),
    ], id="%%x"),
]


@pytest.mark.parametrize("format,expected", test_regex_data)
def test_regex(format, expected):
    assert list(parse_old_format(format)) == expected


test_old_vs_new = [
    pytest.param("%s %s", "{:s} {:s}"),
    pytest.param("%d %d", "{:d} {:d}"),
    pytest.param("%(Dating)s %(Income)2.2f", "{Dating:s} {Income:2.2f}"),
    pytest.param("%s %r", "{:s} {!r}"),
    pytest.param("%10s", "{:>10s}"),
    pytest.param("%-10s", "{:10s}"),
    pytest.param("%.5s", "{:.5s}"),
    pytest.param("%-10.5s", "{:10.5s}"),
    pytest.param("%4d", "{:4d}"),
    pytest.param("%06.2f", "{:06.2f}"),
    pytest.param("%04d", "{:04d}"),
    pytest.param("%+d", "{:+d}"),
    pytest.param("% d", "{: d}"),
    pytest.param("%(first)s %(last)s", "{first:s} {last:s}"),
]


@pytest.mark.parametrize("old,new", test_old_vs_new)
def test_old_vs_new(old, new):
    assert list(parse_old_format(old)) == list(Formatter().parse(new))
