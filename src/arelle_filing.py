"""Read numeric SEC filing facts using Arelle."""

from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from arelle.api.Session import Session
from arelle.RuntimeOptions import RuntimeOptions
from arelle.XmlValidateConst import VALID


def read_processed_filing(filing, cik, user_agent, report_dates):
    if not user_agent or not user_agent.strip():
        raise ValueError("Set SEC_USER_AGENT in .env.")

    url = filing["url"]
    parsed = urlparse(url)

    expected_prefix = (
        "/Archives/edgar/data/"
        f"{int(cik)}/{filing['accession'].replace('-', '')}/"
    )

    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.sec.gov"
        or not parsed.path.startswith(expected_prefix)
    ):
        raise ValueError("Filing URL does not match the company and accession.")

    options = RuntimeOptions(
        entrypointFile=url,
        httpUserAgent=user_agent,
        internetConnectivity="online",
        internetTimeout=30,
        httpsRedirectCache=True,
        keepOpen=True,
        validate=True,
        abortOnMajorError=True,
        logFile="logToBuffer",
        logLevel="ERROR",
        disablePersistentConfig=True,
    )

    records = []
    wanted_dates = set(report_dates)

    with Session() as session:
        session.run(options)

        models = session.get_models()

        if not models:
            raise ValueError("Arelle could not load the filing.")

        for model in models:
            for fact in model.facts:
                if (
                    not fact.isNumeric
                    or fact.isNil
                    or getattr(fact, "xValid", 0) < VALID
                ):
                    continue

                context = fact.context
                unit = fact.unit

                if context is None or unit is None:
                    continue

                if context.hasSegment or context.hasScenario:
                    continue

                scheme, identifier = context.entityIdentifier

                if (
                    scheme.rstrip("/") != "http://www.sec.gov/CIK"
                    or not identifier.isdigit()
                    or int(identifier) != int(cik)
                ):
                    continue

                numerator, denominator = unit.measures

                if denominator or len(numerator) != 1:
                    continue

                measure = numerator[0]

                if (
                    measure.localName != "USD"
                    or measure.namespaceURI
                    != "http://www.xbrl.org/2003/iso4217"
                ):
                    continue

                if context.isInstantPeriod:
                    end = context.instantDate
                    start = None
                elif context.isStartEndPeriod:
                    end = context.endDate
                    start = context.startDatetime.date()
                else:
                    continue

                if end is None or end.isoformat() not in wanted_dates:
                    continue

                if start is not None and not 330 <= (end - start).days <= 380:
                    continue

                try:
                    value = Decimal(str(fact.xValue))
                except (InvalidOperation, ValueError):
                    continue

                if (
                    not value.is_finite()
                    or value != value.to_integral_value()
                ):
                    continue

                parents = []
                relationships = model.relationshipSet(
                    "http://www.xbrl.org/2003/arcrole/summation-item"
                )
                for relationship in relationships.toModelObject(fact.concept):
                    parent = relationship.fromModelObject
                    if parent is not None and parent.qname is not None:
                        parents.append({
                            "concept": parent.qname.localName,
                            "namespace": parent.qname.namespaceURI,
                            "weight": relationship.weight,
                            "role": relationship.linkrole,
                        })

                records.append({
                    "concept": fact.qname.localName,
                    "definition": fact.concept.label(
                        preferredLabel=(
                            "http://www.xbrl.org/2003/role/documentation"
                        ),
                        lang=("en-US", "en"),
                        fallbackToQname=False,
                    ),
                    "period_type": fact.concept.periodType,
                    "balance": fact.concept.balance,
                    "is_monetary": fact.concept.isMonetary,
                    "calculation_parents": parents,
                    "namespace": fact.qname.namespaceURI,
                    "val": int(value),
                    "start": start.isoformat() if start else None,
                    "end": end.isoformat(),
                    "currency": "USD",
                    "unit": "dollars",
                    "source": "SEC original filing",
                    "source_url": url,
                    "accn": filing["accession"],
                    "filed": filing["filed"],
                    "form": filing["form"],
                })

    if not records:
        raise ValueError(
            "No eligible numeric facts were extracted. "
            "The filing may require another supported extraction method."
        )

    return records