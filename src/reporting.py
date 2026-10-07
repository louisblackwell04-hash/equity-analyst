"""Present already-calculated rows. Display rounding happens only here."""
import csv
from pathlib import Path

# key, column heading, display type. This order is the v1 Excel interface.
CSV_COLUMNS = [
    ("cash", "Cash ($ billions)", "billions"),
    ("total_debt", "Debt excluding leases ($ billions)", "billions"),
    ("net_debt", "Net debt excluding leases ($ billions)", "billions"),
    ("equity", "Shareholders' equity ($ billions)", "billions"),
    ("debt_to_equity", "Debt-to-equity excluding leases", "ratio"),
    ("current_ratio", "Current ratio", "ratio"),
    ("quick_ratio", "Quick ratio", "ratio"),
    ("cash_ratio", "Cash ratio including short-term investments", "ratio"),
    ("working_capital", "Working capital ($ billions)", "billions"),
    ("cash_conversion", "Operating cash flow / net income", "ratio"),
]
TERMINAL_METRICS = [
    ("revenue_growth", "Revenue Growth", "percent"),
    ("net_margin", "Net Margin", "percent"),
    ("operating_margin", "Operating Margin", "percent"),
    ("gross_margin", "Gross Margin", "percent"),
    ("fcf", "Free Cash Flow", "billions"),
    ("fcf_margin", "FCF Margin", "percent"),
    ("fcf_growth", "FCF Growth", "percent"),
    ("cash", "Cash and Cash Equivalents ($ billions)", "billions"),
    ("total_debt", "Long-Term Debt + Commercial Paper ($ billions)", "billions"),
    ("net_debt", "Net Debt — Excluding Leases ($ billions)", "billions"),
    ("equity", "Shareholders' Equity ($ billions)", "billions"),
    ("debt_to_equity", "Debt-to-Equity — Excluding Leases", "ratio"),
    ("current_assets", "Current Assets ($ billions)", "billions"),
    ("current_liabilities", "Current Liabilities ($ billions)", "billions"),
    ("current_ratio", "Current Ratio", "ratio"),
    ("short_term_investments", "Short-Term Investments ($ billions)", "billions"),
    ("receivables", "Accounts Receivable ($ billions)", "billions"),
    ("quick_ratio", "Quick Ratio", "ratio"),
    ("cash_ratio", "Cash Ratio — Including Short-Term Investments", "ratio"),
    ("working_capital", "Working Capital ($ billions)", "billions"),
    ("cash_conversion", "Operating Cash Flow / Net Income", "ratio"),
]


def format_value(value, kind, terminal=False):
    if value is None:
        return "Unavailable" if terminal else ""
    if kind == "billions":
        return f"{value / 1_000_000_000:.2f}"
    if kind == "percent":
        return f"{value:.2%}"
    return f"{value:.2f}" + ("x" if terminal else "")


def print_report(rows, ticker=None):
    heading_overrides = {}

    if ticker == "WMT":
        heading_overrides = {
            "total_debt": (
                "Long-Term Debt + Short-Term Borrowings ($ billions)"
            ),
            "gross_margin": (
                "Derived Gross Margin — Total Revenue Basis"
            ),
            "receivables": "Current Receivables ($ billions)",
        }

    for key, heading, kind in TERMINAL_METRICS:
        heading = heading_overrides.get(key, heading)
        print(f"\n{heading}")

        for index, row in enumerate(rows):
            if index == 0 and key.endswith("_growth") and row[key] is None:
                continue

            print(
                row["year"],
                format_value(row.get(key), kind, terminal=True),
            )

def write_summary_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Year"] + [heading for _, heading, _ in CSV_COLUMNS])
        for row in rows:
            writer.writerow([row["year"]] + [format_value(row.get(key), kind)
                                            for key, _, kind in CSV_COLUMNS])
    return path
