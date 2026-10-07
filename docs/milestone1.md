# Milestone 1 verification — 2026-10-07

## Result

Microsoft analysis is separated into retrieval, configuration, pure calculations, output formatting, and Excel generation. Existing commands and workbook layout are preserved. Shared numeric results feed both terminal and CSV; CSV formatting does not recalculate financial metrics.

## Evidence

- Baseline CSV: nine years (2018–2026), eleven columns.
- Retrieved public Microsoft company facts once and ran the pre-refactor script against that snapshot. Its CSV matched the user-saved baseline byte for byte.
- Preserved the used concepts and annual USD records in an offline fixture, with source and retrieval date documented.
- New calculations reproduce the CSV byte for byte and every original terminal section's displayed values.
- Thirteen offline checks cover baseline preservation, missing versus zero data, invalid denominators, negative FCF, missing-year growth, missing cash, annual selection, wrong-company rejection, import safety, and running outside the project directory.
- Generated old and new workbooks in a temporary directory. ZIP package parts matched exactly except the permitted creation/modification timestamps. This includes sheets, values, formulas, formats, navigation links, chart definitions and chart caches. No layout changes were made; the user's open workbook was not overwritten. Reopening in Excel was not repeated during this refactor.
- No dependencies were installed or upgraded. requirements.txt records the installed versions used for verification.

## Intentional changes

- Importing an entry-point script no longer triggers downloads or report writes.
- Output paths resolve from the project folder.
- Empty CSVs and missing SEC identification receive explicit errors.
- Other companies cannot receive Microsoft's manual overrides.
- Missing/nonpositive ratio denominators remain unavailable. Terminal wording is standardized; CSV cells stay blank.
- Growth cannot bridge a missing calendar year.
- A year is retained when any input series contains it, even if cash is absent.

## Deferred to the approved later milestones

Ticker support, fiscal-year generalization, duplicate/restatement handling and filing-period consistency are Milestone 2. Independent reconciliation and revalidation of manual zero assumptions are Milestone 3. Other analyst metrics, valuation, peers and complete metric exports follow those steps.

Existing Microsoft selection rules and manual debt assumptions remain for baseline comparability. Matching the baseline does not independently verify the financial statements.

## Repeat the check

```bash
python3 -m unittest discover -s tests -v
```
