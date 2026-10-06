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

annual_net_income = get_annual_facts(
    msft_data,
    "NetIncomeLoss"
)
annual_operating_income = get_annual_facts(
    msft_data,
    "OperatingIncomeLoss"
)

annual_gross_profit = get_annual_facts(
    msft_data,
    "GrossProfit"
)

print("Revenue Growth")

for i in range(1, len(annual_revenue)):
    current = annual_revenue[i]
    previous = annual_revenue[i - 1]

    growth = (current["val"] / previous["val"]) - 1

    print(current["fy"], f"{growth:.2%}")
net_income_by_year = {}

for item in annual_net_income:
    net_income_by_year[item["fy"]] = item
operating_income_by_year = {}
for item in annual_operating_income:
    operating_income_by_year[item["fy"]] = item
    gross_profit_by_year = {}

for item in annual_gross_profit:
    gross_profit_by_year[item["fy"]] = item
print("\nNet Margin")
for revenue_item in annual_revenue:
    year = revenue_item["fy"]
    net_income_item = net_income_by_year[year]
    net_margin = net_income_item["val"] / revenue_item["val"]

    print(year, f"{net_margin:.2%}")
print("\nOperating Margin")
for revenue_item in annual_revenue:
    year = revenue_item["fy"]
    operating_income_item = operating_income_by_year[year]
    operating_margin = operating_income_item["val"] / revenue_item["val"]

    print(year, f"{operating_margin:.2%}")
print("\nGross Margin")
for revenue_item in annual_revenue:
    year = revenue_item["fy"]
    gross_profit_item = gross_profit_by_year[year]
    gross_margin = gross_profit_item["val"] / revenue_item["val"]

    print(year, f"{gross_margin:.2%}")