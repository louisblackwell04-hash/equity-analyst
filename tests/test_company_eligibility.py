import unittest

from src.company_eligibility import check_company_eligibility


def submissions(sic="3571", forms=None):
    return {
        "sic": sic,
        "filings": {
            "recent": {
                "form": forms if forms is not None else ["10-K"]
            }
        },
    }


class EligibilityTests(unittest.TestCase):
    def setUp(self):
        self.facts = {"facts": {"us-gaap": {"Example": {}}}}

    def test_operating_company_passes(self):
        result = check_company_eligibility(
            submissions(), self.facts
        )
        self.assertEqual(result["status"], "Within initial scope")

    def test_bank_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Financial"):
            check_company_eligibility(submissions("6021"), self.facts)

    def test_reit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "REIT"):
            check_company_eligibility(submissions("6798"), self.facts)

    def test_investment_classification_requires_review(self):
        with self.assertRaisesRegex(ValueError, "require review"):
            check_company_eligibility(submissions("6722"), self.facts)

    def test_foreign_annual_report_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Foreign"):
            check_company_eligibility(
                submissions(forms=["20-F"]), self.facts
            )

    def test_latest_foreign_form_overrides_older_domestic_form(self):
        with self.assertRaisesRegex(ValueError, "Foreign"):
            check_company_eligibility(
                submissions(forms=["20-F", "10-K"]), self.facts
            )

    def test_missing_industry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing or invalid"):
            check_company_eligibility(submissions(None), self.facts)

    def test_missing_us_gaap_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "US-GAAP"):
            check_company_eligibility(submissions(), {"facts": {}})


if __name__ == "__main__":
    unittest.main()