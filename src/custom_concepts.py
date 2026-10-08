"""Conservative classification of supported custom financial concepts."""


import hashlib


STANDARD_NAMESPACES = (
    "http://fasb.org/us-gaap/",
    "https://fasb.org/us-gaap/",
    "http://xbrl.us/us-gaap/",
    "https://xbrl.us/us-gaap/",
)


def classify_custom_fact(record):
    namespace = record.get("namespace", "")

    if not namespace or namespace.startswith(STANDARD_NAMESPACES):
        return None

    if (
        record.get("period_type") != "duration"
        or record.get("balance") != "credit"
        or record.get("is_monetary") is not True
        or type(record.get("val")) is not int
        or record["val"] < 0
    ):
        return None

    definition = " ".join(
        (record.get("definition") or "").lower().split()
    )

    fingerprint = hashlib.sha256(definition.encode()).hexdigest()

    approved_definitions = {
        "8480b224ac25604e94d738bae8e41c0d852fcda7130b4bf1eb93006c2acb094f",
    }

    if fingerprint not in approved_definitions:
        return None

    for parent in record.get("calculation_parents", []):
        if (
            parent.get("concept")
            == "NetCashProvidedByUsedInInvestingActivities"
            and parent.get("namespace", "").startswith(STANDARD_NAMESPACES)
            and parent.get("weight") == -1
        ):
            return "productive_asset_purchases"

    return None