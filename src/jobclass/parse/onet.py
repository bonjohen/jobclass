"""O*NET source file parsers: skills, knowledge, abilities, tasks."""

import csv
import io
from dataclasses import dataclass

from jobclass.parse.common import parse_float, parse_int

PARSER_VERSION = "1.0.0"


@dataclass
class OnetDescriptorRow:
    """Parsed row for skills, knowledge, or abilities."""

    occupation_code: str
    element_id: str
    element_name: str
    scale_id: str
    data_value: float | None
    n: int | None
    standard_error: float | None
    lower_ci: float | None
    upper_ci: float | None
    recommend_suppress: bool
    not_relevant: bool
    date: str | None
    domain_source: str | None
    source_release_id: str
    parser_version: str


@dataclass
class OnetTaskRow:
    """Parsed row for task statements."""

    occupation_code: str
    task_id: str
    task: str
    task_type: str | None
    incumbents_responding: int | None
    date: str | None
    domain_source: str | None
    source_release_id: str
    parser_version: str


@dataclass
class OnetEducationRow:
    """Parsed row for education, training, and experience."""

    occupation_code: str
    element_id: str
    element_name: str
    scale_id: str
    category: int
    data_value: float | None
    n: int | None
    standard_error: float | None
    lower_ci: float | None
    upper_ci: float | None
    recommend_suppress: bool
    not_relevant: bool
    date: str | None
    domain_source: str | None
    source_release_id: str
    parser_version: str


@dataclass
class OnetTechnologyRow:
    """Parsed row for technology skills (tools & technology)."""

    occupation_code: str
    t2_type: str
    example_name: str
    commodity_code: str | None
    commodity_title: str | None
    hot_technology: bool
    date: str | None
    domain_source: str | None
    source_release_id: str
    parser_version: str


def _strip_onet_suffix(code: str) -> str:
    """Strip the .XX suffix from O*NET-SOC codes to get base SOC code."""
    if "." in code:
        return code.rsplit(".", 1)[0]
    return code


def _parse_bool_flag(val: str) -> bool:
    return val.strip().upper() == "Y" if val else False


def parse_onet_descriptors(content: str, source_release_id: str) -> list[OnetDescriptorRow]:
    """Parse O*NET skills, knowledge, or abilities TSV content."""
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    rows = []
    for record in reader:
        rows.append(
            OnetDescriptorRow(
                occupation_code=_strip_onet_suffix(record["O*NET-SOC Code"].strip()),
                element_id=record["Element ID"].strip(),
                element_name=record["Element Name"].strip(),
                scale_id=record["Scale ID"].strip(),
                data_value=parse_float(record["Data Value"]),
                n=parse_int(record["N"]),
                standard_error=parse_float(record["Standard Error"]),
                lower_ci=parse_float(record["Lower CI Bound"]),
                upper_ci=parse_float(record["Upper CI Bound"]),
                recommend_suppress=_parse_bool_flag(record["Recommend Suppress"]),
                not_relevant=_parse_bool_flag(record["Not Relevant"]),
                date=record.get("Date", "").strip() or None,
                domain_source=record.get("Domain Source", "").strip() or None,
                source_release_id=source_release_id,
                parser_version=PARSER_VERSION,
            )
        )
    return rows


def parse_onet_tasks(content: str, source_release_id: str) -> list[OnetTaskRow]:
    """Parse O*NET task statements TSV content."""
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    rows = []
    for record in reader:
        rows.append(
            OnetTaskRow(
                occupation_code=_strip_onet_suffix(record["O*NET-SOC Code"].strip()),
                task_id=record["Task ID"].strip(),
                task=record["Task"].strip(),
                task_type=record.get("Task Type", "").strip() or None,
                incumbents_responding=parse_int(record.get("Incumbents Responding", "")),
                date=record.get("Date", "").strip() or None,
                domain_source=record.get("Domain Source", "").strip() or None,
                source_release_id=source_release_id,
                parser_version=PARSER_VERSION,
            )
        )
    return rows


def parse_onet_education(content: str, source_release_id: str) -> list[OnetEducationRow]:
    """Parse O*NET Education, Training, and Experience TSV content.

    Unlike other O*NET files, this one has a Category column (integer) that
    identifies the education level/training tier, with data_value as a percentage.
    """
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    rows = []
    for record in reader:
        rows.append(
            OnetEducationRow(
                occupation_code=_strip_onet_suffix(record["O*NET-SOC Code"].strip()),
                element_id=record["Element ID"].strip(),
                element_name=record["Element Name"].strip(),
                scale_id=record["Scale ID"].strip(),
                category=parse_int(record["Category"]) or 0,
                data_value=parse_float(record["Data Value"]),
                n=parse_int(record["N"]),
                standard_error=parse_float(record["Standard Error"]),
                lower_ci=parse_float(record["Lower CI Bound"]),
                upper_ci=parse_float(record["Upper CI Bound"]),
                recommend_suppress=_parse_bool_flag(record["Recommend Suppress"]),
                not_relevant=_parse_bool_flag(record["Not Relevant"]),
                date=record.get("Date", "").strip() or None,
                domain_source=record.get("Domain Source", "").strip() or None,
                source_release_id=source_release_id,
                parser_version=PARSER_VERSION,
            )
        )
    return rows


def parse_onet_technology(content: str, source_release_id: str) -> list[OnetTechnologyRow]:
    """Parse O*NET Technology Skills TSV content.

    Unlike descriptor files, this has commodity-based columns (T2 Type, T2 Example,
    Commodity Code, Commodity Title) and a Hot Technology flag. No Scale ID or Data Value.
    """
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    rows = []
    for record in reader:
        rows.append(
            OnetTechnologyRow(
                occupation_code=_strip_onet_suffix(record["O*NET-SOC Code"].strip()),
                t2_type=record["T2 Type"].strip(),
                example_name=record["T2 Example"].strip(),
                commodity_code=record.get("Commodity Code", "").strip() or None,
                commodity_title=record.get("Commodity Title", "").strip() or None,
                hot_technology=_parse_bool_flag(record.get("Hot Technology", "")),
                date=record.get("Date", "").strip() or None,
                domain_source=record.get("Domain Source", "").strip() or None,
                source_release_id=source_release_id,
                parser_version=PARSER_VERSION,
            )
        )
    return rows
