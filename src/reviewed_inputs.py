"""Apply documented, reviewed SEC inputs without replacing existing values."""

import json
import re
from pathlib import Path


def fill_reviewed_inputs(series, path, ticker, cik, report_dates):
    records = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    if not isinstance(records, list):
        raise ValueError("Reviewed inputs must be a JSON list.")

    updated = {
        metric: dict(values)
        for metric, values in series.items()
    }
    sources = {}
    seen = set()
    ticker = ticker.strip().upper()
    expected_cik = str(int(cik)).zfill(10)

    if len({date[:4] for date in report_dates}) != len(report_dates):
        raise ValueError("Multiple reporting dates share the same year.")

    allowed_metrics = {
        "cash",
        "short_term_investments",
        "commercial_paper",
    }

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid reviewed-input record.")

        if record.get("ticker") != ticker:
            continue

        if record.get("cik") != expected_cik:
            raise ValueError("Reviewed input has the wrong company ID.")

        period_end = record.get("period_end")

        if period_end not in report_dates:
            continue

        metric = record.get("metric")
        value = record.get("value")

        if metric not in allowed_metrics:
            raise ValueError(f"Unapproved reviewed metric: {metric}.")

        if type(value) is not int or value < 0:
            raise ValueError("Reviewed values must be nonnegative USD dollars.")

        if (
            record.get("currency") != "USD"
            or record.get("unit") != "dollars"
            or record.get("source") != "Reviewed SEC filing"
        ):
            raise ValueError("Invalid reviewed-input currency, unit or source.")

        for field in ("location", "evidence"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f"Missing reviewed-input {field}.")

        accession = record.get("accession", "")

        if not isinstance(accession, str) or not re.fullmatch(
            r"\d{10}-\d{2}-\d{6}", accession
        ):
            raise ValueError("Invalid SEC accession number.")

        expected_prefix = (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{int(expected_cik)}/{accession.replace('-', '')}/"
        )
        url = record.get("source_url", "")

        if not isinstance(url, str) or not url.startswith(expected_prefix):
            raise ValueError("Source URL does not match the company and filing.")

        key = (period_end, metric)

        if key in seen:
            raise ValueError("Duplicate reviewed input for the same period.")

        seen.add(key)
        year = int(period_end[:4])
        values = updated.setdefault(metric, {})

        if values.get(year) is not None:
            continue

        values[year] = value
        sources.setdefault(str(year), {})[metric] = dict(record)

    return updated, sources
