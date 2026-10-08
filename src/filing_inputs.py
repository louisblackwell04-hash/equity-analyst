"""Merge compatible filing facts into missing analysis inputs."""

from datetime import date

if __package__:
    from .standard_concepts import get_standard_concepts
    from .universal_selection import APPROVED_ALTERNATIVES
    from .custom_concepts import classify_custom_fact
else:
    from standard_concepts import get_standard_concepts
    from universal_selection import APPROVED_ALTERNATIVES
    from custom_concepts import classify_custom_fact


def fill_from_filing(series, records, report_dates, expected_starts=None):
    updated = {
        metric: dict(values)
        for metric, values in series.items()
    }
    sources = {}
    issues = {}
    starts = dict(expected_starts or {})
    flows, balances = get_standard_concepts()

    namespaces = (
        "http://fasb.org/us-gaap/",
        "https://fasb.org/us-gaap/",
        "http://xbrl.us/us-gaap/",
        "https://xbrl.us/us-gaap/",
    )

    for definitions, is_flow in ((flows, True), (balances, False)):
        for metric, preferred in definitions.items():
            concepts = APPROVED_ALTERNATIVES.get(metric, (preferred,))

            for period_end in report_dates:
                year = int(period_end[:4])

                if updated.get(metric, {}).get(year) is not None:
                    continue

                for concept in (*concepts, None):
                    matches = []

                    for record in records:
                        if concept is None:
                            if classify_custom_fact(record) != metric:
                                continue
                        elif (
                            record.get("concept") != concept
                            or not record.get("namespace", "").startswith(namespaces)
                        ):
                            continue

                        if (
                            record.get("end") != period_end
                            or record.get("currency") != "USD"
                            or record.get("unit") != "dollars"
                            or record.get("source") != "SEC original filing"
                            or record.get("form") not in ("10-K", "10-K/A")
                            or type(record.get("val")) is not int
                        ):
                            continue

                        start = record.get("start")

                        if is_flow:
                            if start is None:
                                continue
                            try:
                                days = (
                                    date.fromisoformat(period_end)
                                    - date.fromisoformat(start)
                                ).days
                            except ValueError:
                                continue
                            if not 330 <= days <= 380:
                                continue
                        elif start is not None:
                            continue

                        matches.append(record)

                    if not matches:
                        continue

                    values = {
                        (record["val"], record.get("start"))
                        for record in matches
                    }

                    if len(values) != 1:
                        issues.setdefault(str(year), {})[metric] = (
                            "Conflicting filing values or reporting periods."
                        )
                        break

                    record = matches[0]

                    if is_flow:
                        start = record["start"]
                        if period_end in starts and starts[period_end] != start:
                            issues.setdefault(str(year), {})[metric] = (
                                "Filing flow period differs from selected inputs."
                            )
                            break
                        starts[period_end] = start

                    updated.setdefault(metric, {})[year] = record["val"]
                    sources.setdefault(str(year), {})[metric] = {
                        **record,
                        "selected_concept": record["concept"],
                        "mapping_basis": (
                            "Supported custom definition and calculation relationship"
                            if concept is None else "Standard taxonomy concept"
                        ),
                    }
                    break

    return updated, sources, issues