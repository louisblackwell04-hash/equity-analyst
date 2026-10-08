"""Locate original annual filings for secondary extraction."""
from bs4 import BeautifulSoup
import requests

if __package__:
    from .sec_data import get_company_submissions
else:
    from sec_data import get_company_submissions


def get_annual_filing_documents(cik, user_agent, start_year=2018):
    submissions = get_company_submissions(cik, user_agent)
    documents = []
    seen = set()

    def collect(filings):
        for index, form in enumerate(filings.get("form", [])):
            if form not in ("10-K", "10-K/A"):
                continue

            date = filings["reportDate"][index]
            document = filings["primaryDocument"][index]
            accession = filings["accessionNumber"][index]

            if not date or not document:
                continue

            if int(date[:4]) < start_year or accession in seen:
                continue

            seen.add(accession)

            documents.append({
                "period_end": date,
                "filed": filings["filingDate"][index],
                "accession": accession,
                "form": form,
                "url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/{accession.replace('-', '')}/{document}"
                ),
            })

    collect(submissions["filings"]["recent"])

    for archive in submissions["filings"].get("files", []):
        if archive.get("filingTo", "9999-12-31") < f"{start_year}-01-01":
            continue

        response = requests.get(
            f'https://data.sec.gov/submissions/{archive["name"]}',
            headers={"User-Agent": user_agent},
            timeout=30,
        )
        response.raise_for_status()
        collect(response.json())

    return sorted(
        documents,
        key=lambda item: (item["period_end"], item["filed"]),
        reverse=True,
    )
def _local_name(tag):
    return tag.name.rsplit(":", 1)[-1].lower() if tag.name else ""


def read_filing_facts(filing, user_agent):
    if not user_agent or not user_agent.strip():
        raise ValueError("Set SEC_USER_AGENT in your .env file.")

    url = filing["url"]

    if not url.startswith("https://www.sec.gov/Archives/edgar/data/"):
        raise ValueError("The fallback source must be an SEC filing.")

    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=60,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    def find_local(parent, name):
        return parent.find(
            lambda tag: _local_name(tag) == name
        )

    def text_of(parent, name):
        tag = find_local(parent, name)
        return tag.get_text(strip=True) if tag else None

    contexts = {}

    for tag in soup.find_all(
        lambda tag: _local_name(tag) == "context"
    ):
        period = find_local(tag, "period")

        if period is None:
            continue

        contexts[tag.get("id")] = {
            "entity": text_of(tag, "identifier"),
            "start": text_of(period, "startdate"),
            "end": (
                text_of(period, "instant")
                or text_of(period, "enddate")
            ),
            "has_dimensions": bool(tag.find(
                lambda child: _local_name(child)
                in ("explicitmember", "typedmember")
            )),
        }

    units = {}

    for tag in soup.find_all(
        lambda tag: _local_name(tag) == "unit"
    ):
        measures = tag.find_all(
            lambda child: _local_name(child) == "measure"
        )

        units[tag.get("id")] = {
            "measures": [
                measure.get_text(strip=True) for measure in measures
            ],
            "has_divide": find_local(tag, "divide") is not None,
        }

    for tag in soup.find_all(
        lambda tag: _local_name(tag) == "exclude"
    ):
        tag.decompose()

    facts = []

    for tag in soup.find_all(
        lambda tag: _local_name(tag) == "nonfraction"
    ):
        facts.append({
            "concept": tag.get("name"),
            "raw_text": tag.get_text(" ", strip=True),
            "context": contexts.get(tag.get("contextref")),
            "unit": units.get(tag.get("unitref")),
            "scale": tag.get("scale", "0"),
            "sign": tag.get("sign"),
            "format": tag.get("format"),
            "nil": tag.get("xsi:nil", "").lower() in ("true", "1"),
            "source_url": url,
            "accession": filing["accession"],
        })

    if not facts:
        raise ValueError(
            "No inline numeric facts were found. "
            "This filing needs another extraction method."
        )

    return facts