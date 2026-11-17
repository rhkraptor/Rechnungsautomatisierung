"""Business-rule tests with invented values; no cloud calls or Ground Truth."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from invoice_validation import evaluate_records


class ValidationTests(unittest.TestCase):
    def record(self, identity="example-1", number="DEMO-001"):
        values = {"VendorName": "Example Supplier", "InvoiceId": number,
                  "InvoiceDate": "2026-01-01", "DueDate": "2026-01-31",
                  "SubTotal": "100.00", "TotalTax": "19.00", "InvoiceTotal": "119.00"}
        return {"record_id": identity, "raw": dict(values), "refined": dict(values),
                "source_grounding_validated": True}

    def codes(self, result):
        return {reason["code"] for reason in result["review_reasons"]}

    def test_complete_consistent_agreement_passes_checks_without_approval(self):
        result = evaluate_records([self.record()])[0]
        self.assertEqual(result["status"], "checks_passed")
        self.assertFalse(result["automatic_approval"])

    def test_each_of_seven_fields_is_mandatory_including_due_date(self):
        for field in self.record()["refined"]:
            with self.subTest(field=field):
                record = self.record()
                record["refined"][field] = None
                result = evaluate_records([record])[0]
                self.assertEqual(result["status"], "review_required")
                self.assertIn({"code": "required_field_missing", "field": field}, result["review_reasons"])

    def test_grounded_correction_still_requires_tester_review(self):
        record = self.record()
        record["raw"]["VendorName"] = "EXAMPLE DOCUMENT TITLE"
        result = evaluate_records([record])[0]
        self.assertIn("raw_refined_disagreement", self.codes(result))
        self.assertEqual(result["status"], "review_required")

    def test_invalid_date_requires_review(self):
        record = self.record()
        record["refined"]["DueDate"] = "2026-02-30"
        self.assertIn("invalid_date", self.codes(evaluate_records([record])[0]))

    def test_nonfinite_and_invalid_amounts_require_review(self):
        for value in ("NaN", "Infinity", "not-a-number", True):
            with self.subTest(value=value):
                record = self.record()
                record["refined"]["SubTotal"] = value
                self.assertIn("invalid_amount", self.codes(evaluate_records([record])[0]))

    def test_inconsistent_totals_require_review(self):
        record = self.record()
        record["refined"]["InvoiceTotal"] = "120.00"
        self.assertIn("totals_inconsistent", self.codes(evaluate_records([record])[0]))

    def test_equal_decimals_and_whitespace_do_not_create_disagreement(self):
        record = self.record()
        record["raw"]["InvoiceTotal"] = 119.0
        record["raw"]["VendorName"] = " Example   Supplier "
        self.assertEqual(evaluate_records([record])[0]["status"], "checks_passed")

    def test_suspected_duplicate_flags_both_records_without_deletion(self):
        records = [self.record("example-a"), self.record("example-b")]
        results = evaluate_records(records)
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn("suspected_duplicate", self.codes(result))
            self.assertEqual(result["status"], "review_required")
            self.assertFalse(result["automatic_approval"])
        self.assertEqual(records[0]["refined"]["InvoiceId"], "DEMO-001")

    def test_different_supplier_or_number_not_marked_duplicate(self):
        a = self.record("example-a")
        b = self.record("example-b", "DEMO-002")
        c = self.record("example-c")
        c["raw"]["VendorName"] = c["refined"]["VendorName"] = "Another Example Supplier"
        for result in evaluate_records([a, b, c]):
            self.assertNotIn("suspected_duplicate", self.codes(result))

    def test_missing_keys_do_not_create_false_duplicates(self):
        records = [self.record("example-a", None), self.record("example-b", None)]
        for result in evaluate_records(records):
            self.assertNotIn("suspected_duplicate", self.codes(result))
            self.assertIn("required_field_missing", self.codes(result))

    def test_unvalidated_grounding_requires_review(self):
        record = self.record()
        record["source_grounding_validated"] = False
        self.assertIn("source_grounding_not_validated", self.codes(evaluate_records([record])[0]))

    def test_duplicate_record_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_records([self.record(), self.record()])

    def test_result_does_not_read_embedded_expected_values(self):
        record = self.record()
        record["expected"] = {"VendorName": "Wrong value in unused field"}
        self.assertEqual(evaluate_records([record])[0]["status"], "checks_passed")


if __name__ == "__main__":
    unittest.main()
