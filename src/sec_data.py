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
