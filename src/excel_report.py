"""Generate the existing formatted workbook from the shared summary CSV."""
import json
from datetime import datetime
import argparse
import csv
from pathlib import Path
import xlsxwriter

PROJECT_FOLDER = Path(__file__).resolve().parents[1]


def build_report(csv_path, excel_path):
    csv_path = Path(csv_path)
    excel_path = Path(excel_path)
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError("The summary CSV has no data rows. Run sec_client.py first.")

    rows.sort(key=lambda row: int(row["Year"]))
    metrics = [column for column in rows[0] if column != "Year"]
    metadata_path = csv_path.with_suffix(".metadata.json")

    if not metadata_path.exists():
        raise ValueError(
            "Company metadata is missing. Run sec_client.py first."
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    company_name = metadata["company_name"]
    ticker = metadata["ticker"]
    period_ends = metadata["period_ends"]
    latest_year = rows[-1]["Year"]
    latest_period_end = period_ends[latest_year]

    with xlsxwriter.Workbook(excel_path) as workbook:
        overview = workbook.add_worksheet("Overview")
        sheet = workbook.add_worksheet("Financial History")
        sheet.hide_gridlines(2)
        sheet.set_tab_color("#17365D")

        title = workbook.add_format({
            "bold": True,
            "font_size": 20,
            "font_color": "#FFFFFF",
            "bg_color": "#17365D",
            "valign": "vcenter"
        })

        subtitle = workbook.add_format({
            "font_size": 11,
            "font_color": "#52657A"
        })

        header = workbook.add_format({
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#17365D",
            "align": "center",
            "valign": "vcenter"
        })

        note = workbook.add_format({
            "font_size": 10,
            "font_color": "#52657A",
            "text_wrap": True,
            "valign": "top"
        })

        last_column = len(rows)

        sheet.merge_range(
            0, 0, 0, last_column,
            f"{company_name} Financial History",
            title
        )

        sheet.merge_range(
            1, 0, 1, last_column,
        "Actual fiscal periods. Dollar amounts in USD billions.",
            subtitle
        )

        sheet.set_row(0, 36)
        sheet.set_row(1, 24)
        sheet.set_row(3, 26)
        sheet.set_column(0, 0, 49)
        sheet.set_column(1, last_column, 12)
        sheet.freeze_panes(4, 1)

        period_format = workbook.add_format({
            "font_size": 9,
            "font_color": "#52657A",
            "align": "center",
            "num_format": "yyyy-mm-dd"
        })

        sheet.set_row(2, 22)
        sheet.write(2, 0, "Fiscal period end", subtitle)
        sheet.write(3, 0, "Metric", header)

        for column, row in enumerate(rows, start=1):
            period_end = datetime.strptime(
                period_ends[row["Year"]], "%Y-%m-%d"
            )

            sheet.write_datetime(
                2, column, period_end, period_format
            )
            sheet.write_number(
                3, column, int(row["Year"]), header
            )
        for index, metric in enumerate(metrics):
            row_number = index + 4
            background = "#F0F4F8" if index % 2 == 0 else "#FFFFFF"

            label_format = workbook.add_format({
                "bg_color": background,
                "font_color": "#17365D",
                "valign": "vcenter"
            })

            number_format = workbook.add_format({
                "bg_color": background,
                "font_color": "#17365D",
                "align": "right",
                "num_format": (
                    '#,##0.00;(#,##0.00);0.00'
                    if "($ billions)" in metric
                    else '0.00"x"'
                )
            })

            sheet.set_row(row_number, 25)
            sheet.write(row_number, 0, metric, label_format)

            for column, record in enumerate(rows, start=1):
                value = record[metric]

                if value == "":
                    sheet.write(row_number, column, "n.a.", number_format)
                else:
                    sheet.write_number(
                        row_number, column, float(value), number_format
                    )

        note_row = len(metrics) + 6

        sheet.merge_range(
            note_row, 0, note_row + 1, last_column,
            "Source: SEC company facts and accompanying company metadata. "
            "Debt excludes leases. Net debt subtracts cash and cash "
            "equivalents only. "
            + " ".join(metadata.get("notes", [])),
            note
        )

        sheet.set_landscape()
        sheet.fit_to_pages(1, 1)
        sheet.print_area(0, 0, note_row + 1, last_column)
        sheet.repeat_rows(3)
        overview.hide_gridlines(2)
        overview.set_zoom(120)
        overview.set_top_left_cell("A1")
        overview.set_selection("A1")
        overview.activate()
        overview.set_tab_color("#17365D")
        overview.set_column("A:A", 3)
        overview.set_column("B:B", 48)
        overview.set_column("C:C", 18)
        overview.set_column("D:F", 14)

        overview.merge_range(
            "B2:F3", f"{company_name} Analyst Overview", title
        )

        latest = rows[-1]
        overview.merge_range(
            "B4:F4",
        f"{ticker} — Fiscal year {latest_year} ended {latest_period_end}",
            subtitle
        )

        overview.write("B6", "Metric", header)
        overview.write("C6", "Latest result", header)

        selected_metrics = [
            "Cash ($ billions)",
            "Debt excluding leases ($ billions)",
            "Net debt excluding leases ($ billions)",
            "Shareholders' equity ($ billions)",
            "Debt-to-equity excluding leases",
            "Current ratio",
            "Quick ratio",
            "Cash ratio including short-term investments",
            "Working capital ($ billions)",
            "Operating cash flow / net income"
        ]

        latest_column = xlsxwriter.utility.xl_col_to_name(last_column)

        for index, metric in enumerate(selected_metrics):
            output_row = index + 6
            history_row = metrics.index(metric) + 5
            reference = f"'Financial History'!{latest_column}{history_row}"

            result_format = workbook.add_format({
                "font_color": "#17365D",
                "bg_color": "#F0F4F8" if index % 2 == 0 else "#FFFFFF",
                "align": "right",
                "num_format": (
                    '#,##0.00;(#,##0.00);0.00'
                    if "($ billions)" in metric
                    else '0.00"x"'
                )
            })

            overview.set_row(output_row, 26)
            overview.write(output_row, 1, metric)

            value = latest[metric]
            cached_value = float(value) if value != "" else "n.a."

            overview.write_formula(
                output_row,
                2,
                f'=IF(ISNUMBER({reference}),{reference},"n.a.")',
                result_format,
                cached_value
            )
            metric_keys = {
                "Current ratio": "current_ratio",
                "Quick ratio": "quick_ratio",
                "Cash ratio including short-term investments": "cash_ratio",
            }

            metric_key = metric_keys.get(metric)
            explanation = (
                metadata.get("unavailable_results", {})
                .get(latest_year, {})
                .get(metric_key)
            )

            if explanation:
                overview.write_comment(
                    output_row,
                    2,
                    explanation,
                    {"author": "Equity Analyst Lab"},
                )
        overview.write_url(
            "B17",
            "internal:'Financial History'!A1",
            string="View full financial history"
        )
        debt_chart = workbook.add_chart({"type": "line"})

        chart_metrics = [
            ("Cash ($ billions)", "Cash", "#008080"),
            ("Debt excluding leases ($ billions)", "Debt", "#17365D"),
            ("Net debt excluding leases ($ billions)", "Net debt", "#8497B0")
        ]

        for metric, label, color in chart_metrics:
            history_row = metrics.index(metric) + 4

            debt_chart.add_series({
                "name": label,
                "categories": ["Financial History", 3, 1, 3, last_column],
                "values": [
                    "Financial History",
                    history_row, 1,
                    history_row, last_column
                ],
                "line": {"color": color, "width": 2.5}
            })

        debt_chart.set_title({"name": "Cash and Debt History"})
        debt_chart.set_x_axis({"name": "Fiscal year"})
        debt_chart.set_y_axis({
            "name": "USD billions",
            "num_format": "0",
            "major_gridlines": {
                "visible": True,
                "line": {"color": "#E5EAF0"}
            }
        })
        debt_chart.set_legend({"position": "bottom"})
        debt_chart.set_chartarea({"border": {"none": True}})
        debt_chart.set_size({"width": 760, "height": 340})

        overview.insert_chart("B20", debt_chart)
        liquidity_chart = workbook.add_chart({"type": "line"})

        liquidity_metrics = [
            ("Current ratio", "Current ratio", "#17365D"),
            ("Quick ratio", "Quick ratio", "#008080"),
            (
                "Cash ratio including short-term investments",
                "Cash ratio",
                "#8497B0"
            )
        ]

        for metric, label, color in liquidity_metrics:
            if all(record[metric] == "" for record in rows):
                continue

            history_row = metrics.index(metric) + 4

            liquidity_chart.add_series({
                "name": label,
                "categories": ["Financial History", 3, 1, 3, last_column],
                "values": [
                    "Financial History",
                    history_row, 1,
                    history_row, last_column
                ],
                "line": {"color": color, "width": 2.5}
            })

        liquidity_chart.set_title({"name": "Liquidity Ratio History"})
        liquidity_chart.set_x_axis({"name": "Fiscal year"})
        liquidity_chart.set_y_axis({
            "name": "Ratio (x)",
            "num_format": '0.0"x"',
            "major_gridlines": {
                "visible": True,
                "line": {"color": "#E5EAF0"}
            }
        })
        liquidity_chart.set_legend({"position": "bottom"})
        liquidity_chart.set_chartarea({"border": {"none": True}})
        liquidity_chart.set_size({"width": 760, "height": 340})

        overview.insert_chart("B43", liquidity_chart)

    return excel_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the Microsoft Excel report.")
    parser.add_argument("--input", type=Path, default=PROJECT_FOLDER / "output" / "financial_summary.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_FOLDER / "output" / "financial_report.xlsx")
    args = parser.parse_args(argv)
    path = build_report(args.input, args.output)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
