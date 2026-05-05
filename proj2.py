from __future__ import annotations
import sys
import csv
from typing import *
from dataclasses import dataclass
import dataclasses
import unittest
import math

sys.setrecursionlimit(10_000)


@dataclass(frozen=True)
class Row:
    country: str
    year: Optional[int]
    electricity_and_heat_co2_emissions: Optional[float]
    electricity_and_heat_co2_emissions_per_capita: Optional[float]
    energy_co2_emissions: Optional[float]
    energy_co2_emissions_per_capita: Optional[float]
    total_co2_emissions_excluding_lucf: Optional[float]
    total_co2_emissions_excluding_lucf_per_capita: Optional[float]


@dataclass(frozen=True)
class Node:
    value: Row
    next: Optional[Node]

EXPECTED_HEADER = [
    "country",
    "year",
    "electricity_and_heat_co2_emissions",
    "electricity_and_heat_co2_emissions_per_capita",
    "energy_co2_emissions",
    "energy_co2_emissions_per_capita",
    "total_co2_emissions_excluding_lucf",
    "total_co2_emissions_excluding_lucf_per_capita",
]


def parse_optional_float(s: str) -> Optional[float]:
    """Parse a string into a float, returning None if the string is empty."""
    return None if s == "" else float(s)


def parse_optional_int(s: str) -> Optional[int]:
    """Parse a string into an int, returning None if the string is empty."""
    return None if s == "" else int(s)


def parse_row(fields: list[str]) -> Row:
    """Construct a Row dataclass instance from a list of raw CSV field strings."""
    return Row(
        country=fields[0],
        year=parse_optional_int(fields[1]),
        electricity_and_heat_co2_emissions=parse_optional_float(fields[2]),
        electricity_and_heat_co2_emissions_per_capita=parse_optional_float(fields[3]),
        energy_co2_emissions=parse_optional_float(fields[4]),
        energy_co2_emissions_per_capita=parse_optional_float(fields[5]),
        total_co2_emissions_excluding_lucf=parse_optional_float(fields[6]),
        total_co2_emissions_excluding_lucf_per_capita=parse_optional_float(fields[7]),
    )


def build_linked_list(rows: list[list[str]], index: int) -> Optional[Node]:
    """Recursively build a linked list of Nodes from a list of raw CSV rows, starting at the given index."""
    if index == len(rows):
        return None
    return Node(
        value=parse_row(rows[index]),
        next=build_linked_list(rows, index + 1)
    )


def read_csv_lines(filename: str) -> Optional[Node]:
    """Read a CSV file, validate its header, and return its rows as a linked list of Row nodes."""
    with open(filename, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != EXPECTED_HEADER:
            raise ValueError(f"Unexpected header: {header}")
        rows = list(reader)
    return build_linked_list(rows, 0)

def get_field_value(row: Row, field_name: str) -> Union[str, float, int, None]:
    """Retrieve the value of a named field from a Row, raising an error if the field name is invalid."""
    valid_fields = {f.name for f in dataclasses.fields(row)}
    if field_name not in valid_fields:
        raise ValueError(f"Unknown field name: {field_name}")
    return getattr(row, field_name)

def listlen(data: Optional[Node]) -> int:
    """Recursively count and return the number of nodes in a linked list."""
    if data is None:
        return 0
    return 1 + listlen(data.next)


def row_matches(row: Row, field_name: str, comparison: str, value: Union[str, float, int]) -> bool:
    """Determine whether a Row's field satisfies a given comparison against a target value."""
    if field_name == "country" and comparison != "equal":
        raise ValueError("Only 'equal' comparison is allowed for the 'country' field")
    field_value = get_field_value(row, field_name)
    if field_value is None:
        return False
    if comparison == "equal":
        return field_value == value
    elif comparison == "less_than":
        return field_value < value
    elif comparison == "greater_than":
        return field_value > value
    else:
        raise ValueError(f"Unknown comparison: {comparison}")


def filter_rows(
    data: Optional[Node],
    field_name: str,
    comparison: str,
    value: Union[str, float, int]
) -> Optional[Node]:
    """Recursively filter a linked list, returning a new list containing only nodes whose Row satisfies the given field comparison."""
    if data is None:
        return None
    rest = filter_rows(data.next, field_name, comparison, value)
    if row_matches(data.value, field_name, comparison, value):
        return Node(value=data.value, next=rest)
    return rest