"""SEC retrieval and the existing annual-selection rules, without calculations."""
import json
from datetime import datetime
from pathlib import Path
import requests


def get_company_facts(cik, user_agent):
    if not user_agent or not user_agent.strip():
        raise ValueError("Set SEC_USER_AGENT in the project's .env file before downloading data.")
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json"
    response = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
    response.raise_for_status()
    return response.json()


def load_company_facts(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_annual_facts(company_data, concept):
    """Preserve v1 flow filtering until fiscal-period selection is addressed in M2."""
    records = company_data["facts"]["us-gaap"][concept]["units"]["USD"]
    result = []
    for item in records:
        end_year = int(item["end"][:4])
        if item["form"] == "10-K" and item["fy"] == end_year:
            if "start" in item:
                start = datetime.strptime(item["start"], "%Y-%m-%d")
                end = datetime.strptime(item["end"], "%Y-%m-%d")
                if (end - start).days > 300:
                    result.append(item)
            else:
                result.append(item)
    return result


def get_year_end_balances(company_data, concept, year_end="-06-30"):
    records = company_data["facts"]["us-gaap"][concept]["units"]["USD"]
    selected = {}
    for item in records:
        if item["form"] != "10-K" or "start" in item:
            continue
        if not item["end"].endswith(year_end):
            continue
        year = int(item["end"][:4])
        previous = selected.get(year)
        if previous is None or item["filed"] > previous["filed"]:
            selected[year] = item
    return selected


def extract_inputs(company_data):
    from company_config import (CIK, FLOW_CONCEPTS, BALANCE_CONCEPTS,
                                FISCAL_YEAR_END, COMMERCIAL_PAPER_OVERRIDES)
    if int(company_data["cik"]) != int(CIK):
        raise ValueError("Milestone 1 supports Microsoft only. Other companies are planned for Milestone 2.")
    series = {}
    for key, concept in FLOW_CONCEPTS.items():
        series[key] = {item["fy"]: item["val"] for item in get_annual_facts(company_data, concept)}
    for key, concept in BALANCE_CONCEPTS.items():
        series[key] = {year: item["val"] for year, item in
                       get_year_end_balances(company_data, concept, FISCAL_YEAR_END).items()}
    for year, override in COMMERCIAL_PAPER_OVERRIDES.items():
        series["commercial_paper"][year] = override["value"]
    return series

def get_company_submissions(cik, user_agent):
    if not user_agent or not user_agent.strip():
        raise ValueError("Set SEC_USER_AGENT in your .env file.")

    url = (
        "https://data.sec.gov/submissions/"
        f"CIK{str(cik).zfill(10)}.json"
    )

    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=30,
    )
    response.raise_for_status()

    return response.json()
def get_annual_report_dates(cik, user_agent, start_year=2018):
    submissions = get_company_submissions(cik, user_agent)
    dates = set()

    def collect_dates(filings):
        for form, date in zip(
            filings.get("form", []),
            filings.get("reportDate", []),
        ):
            if form == "10-K" and date:
                if int(date[:4]) >= start_year:
                    dates.add(date)

    collect_dates(submissions["filings"]["recent"])

    for archive in submissions["filings"].get("files", []):
        if archive.get("filingTo", "9999-12-31") < f"{start_year}-01-01":
            continue

        response = requests.get(
            f'https://data.sec.gov/submissions/{archive["name"]}',
            headers={"User-Agent": user_agent},
            timeout=30,
        )
        response.raise_for_status()
        collect_dates(response.json())

    return sorted(dates)
def get_balances_for_dates(company_data, concept, report_dates):
    fact = company_data["facts"]["us-gaap"].get(concept, {})
    records = fact.get("units", {}).get("USD", [])
    selected = {date: None for date in report_dates}

    for item in records:
        if item["form"] not in ("10-K", "10-K/A"):
            continue

        if "start" in item or item["end"] not in selected:
            continue

        date = item["end"]
        previous = selected[date]

        filing_order = (item["filed"], item["accn"])
        previous_order = (
            (previous["filed"], previous["accn"])
            if previous is not None else ("", "")
        )

        if filing_order > previous_order:
            selected[date] = item

    return selected
def get_flows_for_dates(company_data, concept, report_dates):
    fact = company_data["facts"]["us-gaap"].get(concept, {})
    records = fact.get("units", {}).get("USD", [])
    selected = {date: None for date in report_dates}

    for item in records:
        if item["form"] not in ("10-K", "10-K/A"):
            continue

        if "start" not in item or item["end"] not in selected:
            continue

        start = datetime.strptime(item["start"], "%Y-%m-%d")
        end = datetime.strptime(item["end"], "%Y-%m-%d")
        days = (end - start).days

        if not 330 <= days <= 380:
            continue

        date = item["end"]
        previous = selected[date]

        filing_order = (item["filed"], item["accn"])
        previous_order = (
            (previous["filed"], previous["accn"])
            if previous is not None else ("", "")
        )

        if filing_order > previous_order:
            selected[date] = item

    return selected
def get_financial_records(
    company_data,
    report_dates,
    flow_concepts,
    balance_concepts,
):
    selected = {}

    for metric, concept in flow_concepts.items():
        selected[metric] = get_flows_for_dates(
            company_data, concept, report_dates
        )

    for metric, concept in balance_concepts.items():
        selected[metric] = get_balances_for_dates(
            company_data, concept, report_dates
        )

    return selected
def extract_inputs_for_dates(company_data, report_dates, ticker):
    if __package__:
        from .company_config import get_company_concepts
    else:
        from company_config import get_company_concepts

    flows, balances = get_company_concepts(ticker)

    records = get_financial_records(
        company_data,
        report_dates,
        flows,
        balances,
    )

    series = {}

    for metric, annual_records in records.items():
        series[metric] = {}

        for date, record in annual_records.items():
            year = int(date[:4])
            series[metric][year] = (
                record["val"] if record is not None else None
            )

    return series