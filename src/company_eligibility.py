"""Screen companies before running the operating-company analysis."""


def check_company_eligibility(submissions, company_facts):
    raw_sic = submissions.get("sic")

    try:
        sic = int(raw_sic)
    except (TypeError, ValueError):
        raise ValueError(
            "The company's industry classification is missing or invalid."
        )

    if not 100 <= sic <= 9999:
        raise ValueError(
            "The company's industry classification needs review."
        )

    if sic == 6798:
        raise ValueError(
            "REITs require a dedicated real-estate analysis model."
        )

    if 6000 <= sic <= 6499:
        raise ValueError(
            "Financial and insurance companies require a dedicated model."
        )

    if 6700 <= sic <= 6799:
        raise ValueError(
            "Holding, investment, and blank-check classifications "
            "require review before using this model."
        )

    recent = submissions.get("filings", {}).get("recent", {})
    annual_form = next(
        (
            form.removesuffix("/A")
            for form in recent.get("form", [])
            if form.removesuffix("/A") in ("10-K", "20-F", "40-F")
        ),
        None,
    )

    if annual_form in ("20-F", "40-F"):
        raise ValueError(
            "Foreign-issuer annual reports are outside this release's scope."
        )

    if annual_form != "10-K":
        raise ValueError(
            "No recent supported annual report was found."
        )

    if not company_facts.get("facts", {}).get("us-gaap"):
        raise ValueError(
            "US-GAAP company facts are unavailable."
        )

    return {
        "sic": sic,
        "industry": submissions.get("sicDescription", ""),
        "annual_form": annual_form,
        "status": "Within initial scope",
    }