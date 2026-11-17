"""Offline checks for a source-grounded, single-call refinement experiment."""
import importlib.util
from pathlib import Path
import sys
import unittest
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refine_invoice as refine


class RefinementTests(unittest.TestCase):
    def test_single_call_guard_cannot_be_claimed_twice(self):
        root = refine.ROOT / "private" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            marker = Path(folder) / "guard.json"
            refine.claim_single_call(marker, "first")
            with self.assertRaisesRegex(refine.Blocked, "single_call_approval_already_consumed"):
                refine.claim_single_call(marker, "second")
            self.assertIn('"first"', marker.read_text())

    def test_request_has_output_cap_and_only_source_evidence(self):
        body = refine.build_payload("Example Supplier\nInvoice DEMO-123", "example-deployment")
        self.assertEqual(body["max_completion_tokens"], 1024)
        self.assertEqual(body["reasoning_effort"], "minimal")
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(body["messages"][1]["content"], "Example Supplier\nInvoice DEMO-123")
        self.assertNotIn("expected", body["messages"][0]["content"].lower())

    def test_endpoint_does_not_accept_untrusted_host_or_userinfo(self):
        self.assertEqual(refine.validate_endpoint("https://example.openai.azure.com/"),
                         "https://example.openai.azure.com")
        for url in ("http://example.openai.azure.com", "https://localhost",
                    "https://example.openai.azure.com@evil.invalid", "https://example.openai.azure.com/?key=x"):
            with self.subTest(url=url), self.assertRaises(refine.Blocked):
                refine.validate_endpoint(url)

    def empty_fields(self):
        return {name: {"value": None, "evidence": None, **(
            {"currency": None} if name in refine.MONEY else {})} for name in refine.FIELDS}

    def test_supplier_value_must_be_grounded_and_cannot_be_invented(self):
        fields = self.empty_fields()
        fields["VendorName"] = {"value": "Invented Supplier", "evidence": "Example Supplier"}
        with self.assertRaises(refine.Blocked):
            refine.validate_fields(fields, "Example Supplier")

    def test_source_evidence_must_exist(self):
        fields = self.empty_fields()
        fields["VendorName"] = {"value": "Example Supplier", "evidence": "Example Supplier"}
        with self.assertRaises(refine.Blocked):
            refine.validate_fields(fields, "Document without that name")

    def test_source_grounding_accepts_dates_and_decimal_normalization(self):
        fields = self.empty_fields()
        fields["VendorName"] = {"value": "Example Supplier", "evidence": "Example Supplier"}
        fields["InvoiceDate"] = {"value": "2026-01-01", "evidence": "01.01.2026"}
        fields["InvoiceTotal"] = {"value": "119.00", "evidence": "119,00", "currency": "EUR"}
        result = refine.validate_fields(fields, "Example Supplier\n01.01.2026\nEUR 119,00")
        self.assertEqual(result["analyzeResult"]["documents"][0]["fields"]["InvoiceTotal"]
                         ["valueCurrency"]["amount"], "119.00")

    def test_incorrect_normalized_amount_is_rejected(self):
        fields = self.empty_fields()
        fields["InvoiceTotal"] = {"value": "120", "evidence": "119,00", "currency": "EUR"}
        with self.assertRaises(refine.Blocked):
            refine.validate_fields(fields, "EUR 119,00")

    def test_null_values_are_preserved_not_filled(self):
        result = refine.validate_fields(self.empty_fields(), "Example Supplier")
        self.assertEqual(result["analyzeResult"]["documents"][0]["fields"]["VendorName"], {})

    def test_old_inventory_wrapper_is_supported(self):
        inventory = {"accounts": [{"name": "example-account", "group": "example-group",
                                  "deployments": [{"value": [{"name": "example-deployment",
                                  "model": "gpt-5-mini", "state": "Succeeded"}]}]}]}
        self.assertEqual(refine.select_deployment(inventory)[1]["name"], "example-deployment")


if __name__ == "__main__":
    unittest.main()
