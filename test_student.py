from __future__ import annotations
import sys
import csv
import unittest
import dataclasses
from typing import *
from dataclasses import dataclass

sys.setrecursionlimit(10_000)

from proj2 import (
    Row, Node,
    parse_optional_float, parse_optional_int, parse_row,
    listlen, build_linked_list, read_csv_lines,
    get_field_value, row_matches, filter_rows,
)



def linked_list_to_python_list(data: Optional[Node]) -> list[Row]:
    """Convert a linked list to a plain Python list for easy assertion."""
    if data is None:
        return []
    return [data.value] + linked_list_to_python_list(data.next)



ROW_USA = Row(
    country="United States", year=2020,
    electricity_and_heat_co2_emissions=2000.5,
    electricity_and_heat_co2_emissions_per_capita=6.05,
    energy_co2_emissions=5000.1,
    energy_co2_emissions_per_capita=15.12,
    total_co2_emissions_excluding_lucf=5800.3,
    total_co2_emissions_excluding_lucf_per_capita=17.54,
)

ROW_CHINA = Row(
    country="China", year=2020,
    electricity_and_heat_co2_emissions=4500.2,
    electricity_and_heat_co2_emissions_per_capita=3.12,
    energy_co2_emissions=9800.7,
    energy_co2_emissions_per_capita=6.80,
    total_co2_emissions_excluding_lucf=10500.4,
    total_co2_emissions_excluding_lucf_per_capita=7.29,
)

ROW_BRAZIL = Row(
    country="Brazil", year=2019,
    electricity_and_heat_co2_emissions=120.1,
    electricity_and_heat_co2_emissions_per_capita=0.57,
    energy_co2_emissions=None,
    energy_co2_emissions_per_capita=None,
    total_co2_emissions_excluding_lucf=None,
    total_co2_emissions_excluding_lucf_per_capita=None,
)

ROW_FRANCE = Row(
    country="France", year=2020,
    electricity_and_heat_co2_emissions=None,
    electricity_and_heat_co2_emissions_per_capita=None,
    energy_co2_emissions=320.1,
    energy_co2_emissions_per_capita=4.77,
    total_co2_emissions_excluding_lucf=400.5,
    total_co2_emissions_excluding_lucf_per_capita=5.97,
)



class TestRowAndNode(unittest.TestCase):
    """Row and Node are frozen dataclasses with the correct fields."""

    def test_row_is_frozen(self):
        with self.assertRaises(Exception):
            ROW_USA.country = "Canada"

    def test_row_fields(self):
        expected = {
            "country", "year",
            "electricity_and_heat_co2_emissions",
            "electricity_and_heat_co2_emissions_per_capita",
            "energy_co2_emissions",
            "energy_co2_emissions_per_capita",
            "total_co2_emissions_excluding_lucf",
            "total_co2_emissions_excluding_lucf_per_capita",
        }
        actual = {f.name for f in dataclasses.fields(ROW_USA)}
        self.assertEqual(actual, expected)

    def test_node_holds_row_and_next(self):
        node = Node(value=ROW_USA, next=None)
        self.assertEqual(node.value, ROW_USA)
        self.assertIsNone(node.next)

    def test_node_chain(self):
        tail = Node(value=ROW_CHINA, next=None)
        head = Node(value=ROW_USA, next=tail)
        self.assertEqual(head.next.value, ROW_CHINA)

    def test_row_with_missing_values(self):
        self.assertIsNone(ROW_BRAZIL.energy_co2_emissions)
        self.assertIsNone(ROW_FRANCE.electricity_and_heat_co2_emissions)



class TestParseHelpers(unittest.TestCase):
    """parse_optional_float and parse_optional_int handle blank strings."""

    def test_float_empty(self):
        self.assertIsNone(parse_optional_float(""))

    def test_float_value(self):
        self.assertAlmostEqual(parse_optional_float("3.14"), 3.14)

    def test_int_empty(self):
        self.assertIsNone(parse_optional_int(""))

    def test_int_value(self):
        self.assertEqual(parse_optional_int("2020"), 2020)


class TestParseRow(unittest.TestCase):
    """parse_row converts a list of strings into a Row."""

    def test_full_row(self):
        fields = [
            "United States", "2020", "2000.5", "6.05",
            "5000.1", "15.12", "5800.3", "17.54",
        ]
        row = parse_row(fields)
        self.assertEqual(row.country, "United States")
        self.assertEqual(row.year, 2020)
        self.assertAlmostEqual(row.electricity_and_heat_co2_emissions, 2000.5)

    def test_row_with_missing(self):
        fields = ["Brazil", "2019", "120.1", "0.57", "", "", "", ""]
        row = parse_row(fields)
        self.assertIsNone(row.energy_co2_emissions)
        self.assertIsNone(row.total_co2_emissions_excluding_lucf)


class TestReadCsvLines(unittest.TestCase):
    """read_csv_lines builds a linked list from a CSV file."""

    def test_returns_node(self):
        data = read_csv_lines("sample.csv")
        self.assertIsInstance(data, Node)

    def test_first_row_country(self):
        data = read_csv_lines("sample.csv")
        self.assertEqual(data.value.country, "United States")


class TestListlen(unittest.TestCase):
    """listlen recursively counts nodes."""

    def test_empty(self):
        self.assertEqual(listlen(None), 0)

    def test_single(self):
        node = Node(value=ROW_USA, next=None)
        self.assertEqual(listlen(node), 1)

    def test_multiple(self):
        data = read_csv_lines("some-ghg-emissions.csv")
        self.assertGreater(listlen(data), 0) 

    def test_two_nodes(self):
        node = Node(ROW_USA, Node(ROW_CHINA, None))
        self.assertEqual(listlen(node), 2)


# ── Task 4: filter_rows ───────────────────────────────────────────────────────

class TestGetFieldValue(unittest.TestCase):
    """get_field_value retrieves a field from a Row by name."""

    def test_country(self):
        self.assertEqual(get_field_value(ROW_USA, "country"), "United States")

    def test_numeric_field(self):
        self.assertAlmostEqual(
            get_field_value(ROW_USA, "electricity_and_heat_co2_emissions"), 2000.5
        )

    def test_missing_field_raises(self):
        with self.assertRaises(ValueError):
            get_field_value(ROW_USA, "not_a_field")

    def test_none_field(self):
        self.assertIsNone(get_field_value(ROW_BRAZIL, "energy_co2_emissions"))


class TestRowMatches(unittest.TestCase):
    """row_matches applies comparisons correctly."""

    def test_equal_country(self):
        self.assertTrue(row_matches(ROW_USA, "country", "equal", "United States"))

    def test_equal_country_false(self):
        self.assertFalse(row_matches(ROW_USA, "country", "equal", "China"))

    def test_greater_than(self):
        self.assertTrue(
            row_matches(ROW_CHINA, "electricity_and_heat_co2_emissions", "greater_than", 1000.0)
        )

    def test_less_than(self):
        self.assertTrue(
            row_matches(ROW_BRAZIL, "electricity_and_heat_co2_emissions", "less_than", 200.0)
        )

    def test_none_field_skipped(self):
        self.assertFalse(
            row_matches(ROW_BRAZIL, "energy_co2_emissions", "greater_than", 0.0)
        )

    def test_country_non_equal_raises(self):
        with self.assertRaises(ValueError):
            row_matches(ROW_USA, "country", "less_than", "China")

    def test_unknown_comparison_raises(self):
        with self.assertRaises(ValueError):
            row_matches(ROW_USA, "year", "between", 2020)


class TestFilterRows(unittest.TestCase):
    """filter_rows returns a filtered linked list."""

    def test_filter_by_country(self):
        data = read_csv_lines("sample.csv")
        result = filter_rows(data, "country", "equal", "China")
        rows = linked_list_to_python_list(result)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].country, "China")

    def test_filter_greater_than(self):
        data = read_csv_lines("sample.csv")
        result = filter_rows(data, "electricity_and_heat_co2_emissions", "greater_than", 1000.0)
        rows = linked_list_to_python_list(result)
        self.assertTrue(all(
            r.electricity_and_heat_co2_emissions > 1000.0 for r in rows
        ))

    def test_filter_skips_none(self):
        data = read_csv_lines("sample.csv")
        result = filter_rows(data, "energy_co2_emissions", "greater_than", 0.0)
        rows = linked_list_to_python_list(result)
        self.assertTrue(all(r.energy_co2_emissions is not None for r in rows))

    def test_filter_no_match_returns_none(self):
        data = read_csv_lines("sample.csv")
        result = filter_rows(data, "country", "equal", "Antarctica")
        self.assertIsNone(result)

    def test_filter_preserves_order(self):
        data = read_csv_lines("sample.csv")
        result = filter_rows(data, "year", "equal", 2020)
        rows = linked_list_to_python_list(result)
        countries = [r.country for r in rows]
        self.assertEqual(countries, sorted(countries, key=lambda c: countries.index(c)))


if __name__ == "__main__":
    unittest.main()
