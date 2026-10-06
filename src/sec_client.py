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
        end_year = int(item["end"][:4])

        if item["form"] == "10-K" and item["fy"] == end_year:
            if "start" in item:
                start = datetime.strptime(item["start"], "%Y-%m-%d")
                end = datetime.strptime(item["end"], "%Y-%m-%d")
                days = (end - start).days

                if days > 300:
                    annual_facts.append(item)
            else:
                annual_facts.append(item)

    return annual_facts
def get_year_end_balances(company_data, concept):
    records = company_data["facts"]["us-gaap"][concept]["units"]["USD"]
    balances_by_year = {}

    for item in records:
        if item["form"] != "10-K" or "start" in item:
            continue

        if not item["end"].endswith("-06-30"):
            continue

        year = int(item["end"][:4])
        previous = balances_by_year.get(year)

        if previous is None or item["filed"] > previous["filed"]:
            balances_by_year[year] = item

    return balances_by_year
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

annual_operating_cash_flow = get_annual_facts(
    msft_data,
    "NetCashProvidedByUsedInOperatingActivities"
)
annual_capex = get_annual_facts(
    msft_data,
    "PaymentsToAcquirePropertyPlantAndEquipment"
)
cash_by_year = get_year_end_balances(
    msft_data,
    "CashAndCashEquivalentsAtCarryingValue"
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
operating_cash_flow_by_year = {}

for item in annual_operating_cash_flow:
    operating_cash_flow_by_year[item["fy"]] = item
capex_by_year = {}

for item in annual_capex:
    capex_by_year[item["fy"]] = item
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
print("\nFree Cash Flow")
for revenue_item in annual_revenue:
    year = revenue_item["fy"]
    operating_cash_flow_item = operating_cash_flow_by_year[year]
    capex_item = capex_by_year[year]
    free_cash_flow = operating_cash_flow_item["val"] - capex_item["val"]
    print(year, f"{free_cash_flow / 1_000_000_000:.2f}")
print("\nFCF Margin")
for revenue_item in annual_revenue:
    year = revenue_item["fy"]
    operating_cash_flow_item = operating_cash_flow_by_year[year]
    capex_item = capex_by_year[year]
    free_cash_flow = operating_cash_flow_item["val"] - capex_item["val"]
    fcf_margin = free_cash_flow / revenue_item["val"]
    print(year, f"{fcf_margin:.2%}")
print("\nFCF Growth")
annual_fcf = []

for revenue_item in annual_revenue:
    year = revenue_item["fy"]
    operating_cash_flow_item = operating_cash_flow_by_year[year]
    capex_item = capex_by_year[year]
    free_cash_flow = operating_cash_flow_item["val"] - capex_item["val"]
    annual_fcf.append(free_cash_flow)

for i in range(1, len(annual_fcf)):
    growth = (annual_fcf[i] / annual_fcf[i - 1]) - 1
    year = annual_revenue[i]["fy"]
    print(year, f"{growth:.2%}")
print("\nCash and Cash Equivalents ($ billions)")

for item in annual_revenue:
    year = item["fy"]

    if year in cash_by_year:
        cash = cash_by_year[year]["val"]
        print(year, f"{cash / 1_000_000_000:.2f}")
debt_by_year = get_year_end_balances(
    msft_data,
    "LongTermDebtNoncurrent"
)
current_debt_by_year = get_year_end_balances(
    msft_data,
    "LongTermDebtCurrent"
)
records = msft_data["facts"]["us-gaap"]["CommercialPaper"]["units"]["USD"]
commercial_paper_by_year = get_year_end_balances(
    msft_data,
    "CommercialPaper"
)
# Fill gaps checked against Microsoft's annual reports.
commercial_paper_by_year[2020] = {"val": 0}
commercial_paper_by_year[2021] = {"val": 0}
commercial_paper_by_year[2022] = {"val": 0}
# Manually reviewed against the 2026 balance sheet and debt note.
commercial_paper_by_year[2026] = {"val": 0}
print("\nLong-Term Debt + Commercial Paper ($ billions)")

for year in sorted(debt_by_year):
    if year >= 2018:
        if year in current_debt_by_year and year in commercial_paper_by_year:
            total = (
                debt_by_year[year]["val"]
                + current_debt_by_year[year]["val"]
                + commercial_paper_by_year[year]["val"]
            )
            print(year, f"{total / 1_000_000_000:.2f}")
        else:
            print(year, "Unavailable")
print("\nNet Debt — Excluding Leases ($ billions)")

for year in sorted(debt_by_year):
    if year >= 2018:
        if (
            year in current_debt_by_year
            and year in commercial_paper_by_year
            and year in cash_by_year
        ):
            total_debt = (
                debt_by_year[year]["val"]
                + current_debt_by_year[year]["val"]
                + commercial_paper_by_year[year]["val"]
            )
            net_debt = total_debt - cash_by_year[year]["val"]
            print(year, f"{net_debt / 1_000_000_000:.2f}")
        else:
            print(year, "Unavailable")
equity_by_year = get_year_end_balances(
    msft_data,
    "StockholdersEquity"
)

print("\nShareholders' Equity ($ billions)")

for year in sorted(equity_by_year):
    if year >= 2018:
        value = equity_by_year[year]["val"]
        print(year, f"{value / 1_000_000_000:.2f}")
print("\nDebt-to-Equity — Excluding Leases")

for year in sorted(equity_by_year):
    if year >= 2018:
        if (
            year in debt_by_year
            and year in current_debt_by_year
            and year in commercial_paper_by_year
        ):
            total_debt = (
                debt_by_year[year]["val"]
                + current_debt_by_year[year]["val"]
                + commercial_paper_by_year[year]["val"]
            )
            equity = equity_by_year[year]["val"]

            if equity > 0:
                ratio = total_debt / equity
                print(year, f"{ratio:.2f}x")
            else:
                print(year, "Not meaningful: equity is zero or negative")
        else:
            print(year, "Unavailable")       
current_assets_by_year = get_year_end_balances(
    msft_data,
    "AssetsCurrent"
)

print("\nCurrent Assets ($ billions)")

for year in sorted(current_assets_by_year):
    if year >= 2018:
        value = current_assets_by_year[year]["val"]
        print(year, f"{value / 1_000_000_000:.2f}")
current_liabilities_by_year = get_year_end_balances(
    msft_data,
    "LiabilitiesCurrent"
)

print("\nCurrent Liabilities ($ billions)")

for year in sorted(current_liabilities_by_year):
    if year >= 2018:
        value = current_liabilities_by_year[year]["val"]
        print(year, f"{value / 1_000_000_000:.2f}")
print("\nCurrent Ratio")

for year in sorted(current_assets_by_year):
    if year >= 2018:
        if year in current_liabilities_by_year:
            assets = current_assets_by_year[year]["val"]
            liabilities = current_liabilities_by_year[year]["val"]

            if liabilities > 0:
                ratio = assets / liabilities
                print(year, f"{ratio:.2f}x")
            else:
                print(year, "Not meaningful: liabilities are zero or negative")
        else:
            print(year, "Unavailable")
short_term_investments_by_year = get_year_end_balances(
    msft_data,
    "ShortTermInvestments"
)

print("\nShort-Term Investments ($ billions)")

for year in sorted(short_term_investments_by_year):
    if year >= 2018:
        value = short_term_investments_by_year[year]["val"]
        print(year, f"{value / 1_000_000_000:.2f}")
receivables_by_year = get_year_end_balances(
    msft_data,
    "AccountsReceivableNetCurrent"
)

print("\nAccounts Receivable ($ billions)")

for year in sorted(receivables_by_year):
    if year >= 2018:
        value = receivables_by_year[year]["val"]
        print(year, f"{value / 1_000_000_000:.2f}")
print("\nQuick Ratio")

for year in sorted(current_liabilities_by_year):
    if year >= 2018:
        if (
            year in cash_by_year
            and year in short_term_investments_by_year
            and year in receivables_by_year
        ):
            quick_assets = (
                cash_by_year[year]["val"]
                + short_term_investments_by_year[year]["val"]
                + receivables_by_year[year]["val"]
            )
            liabilities = current_liabilities_by_year[year]["val"]

            if liabilities > 0:
                ratio = quick_assets / liabilities
                print(year, f"{ratio:.2f}x")
            else:
                print(year, "Not meaningful: liabilities are zero or negative")
        else:
            print(year, "Unavailable")       