import os
from datetime import datetime
import requests
from dotenv import load_dotenv


load_dotenv()

user_agent = os.getenv("SEC_USER_AGENT")

headers = {
    "User-Agent": user_agent
}


def get_company_facts(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    return data

def get_annual_facts(company_data, concept):
    fact = company_data["facts"]["us-gaap"][concept]
    annual_facts = []

    for item in fact["units"]["USD"]:
        start = datetime.strptime(item["start"], "%Y-%m-%d")
        end = datetime.strptime(item["end"], "%Y-%m-%d")

        days = (end - start).days
        end_year = int(item["end"][:4])

        if item["form"] == "10-K" and item["fy"] == end_year and days > 300:
            annual_facts.append(item)

    return annual_facts
msft_data = get_company_facts("0000789019")

annual_revenue = get_annual_facts(
    msft_data,
    "RevenueFromContractWithCustomerExcludingAssessedTax"
)
for i in range(1, len(annual_revenue)):
    current = annual_revenue[i]
    previous = annual_revenue[i - 1]

    growth = (current["val"] / previous["val"]) - 1

    print(current["fy"], f"{growth:.2%}")


