"""Offline checks; invented fixtures, never live service calls."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import tempfile
import zipfile

SPEC = importlib.util.spec_from_file_location(
    "extract_invoice", Path(__file__).resolve().parents[1] / "scripts/extract_invoice.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "VendorName": "Example Supplier", "InvoiceId": "DEMO-001",
            "InvoiceDate": "2026-01-01", "DueDate": "2026-01-31",
            "SubTotal": "100", "TotalTax": "19", "InvoiceTotal": "119",
        }
        fields = {
            name: {"valueString": value, "confidence": 0.9}
            for name, value in self.expected.items()
        }
        for name in ("InvoiceDate", "DueDate"):
            fields[name] = {"valueDate": self.expected[name]}
        for name in ("SubTotal", "TotalTax", "InvoiceTotal"):
            fields[name] = {"valueCurrency": {
                "amount": float(self.expected[name]), "currencyCode": "EUR"
            }}
        self.response = {"status": "succeeded", "analyzeResult": {
            "documents": [{"fields": fields}]
        }}

    def test_all_seven_fields_match(self):
        rows = runner.compare(self.response, self.expected)
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["match"] for row in rows))

    def test_missing_field_is_not_filled_from_content(self):
        self.response["analyzeResult"]["documents"][0]["fields"]["InvoiceId"] = {
            "content": "DEMO-001"
        }
        row = next(r for r in runner.compare(self.response, self.expected)
                   if r["field"] == "InvoiceId")
        self.assertFalse(row["match"])
        self.assertIsNone(row["actual"])

    def test_wrong_total_and_wrong_currency_fail(self):
        fields = self.response["analyzeResult"]["documents"][0]["fields"]
        fields["InvoiceTotal"]["valueCurrency"]["amount"] = 120
        fields["TotalTax"]["valueCurrency"]["currencyCode"] = "USD"
        rows = {r["field"]: r for r in runner.compare(self.response, self.expected)}
        self.assertFalse(rows["InvoiceTotal"]["match"])
        self.assertFalse(rows["TotalTax"]["match"])

    def test_two_documents_cannot_silently_use_first(self):
        self.response["analyzeResult"]["documents"] *= 2
        with self.assertRaises(runner.Blocked):
            runner.compare(self.response, self.expected)

    def test_failed_operation_is_not_a_comparison_success(self):
        self.response["status"] = "failed"
        with self.assertRaises(runner.Blocked):
            runner.compare(self.response, self.expected)


class TransportTests(unittest.TestCase):
    def test_http_auth_failure_does_not_echo_sensitive_error(self):
        error = HTTPError("https://example.invalid/private", 403, "private-detail", {}, None)
        with patch.object(runner, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaisesRegex(runner.Blocked, "^http_status_403$"):
                runner.request("https://example.invalid", {"Authorization": "placeholder"})

    def test_untrusted_endpoint_rejected(self):
        for endpoint in ("http://example.invalid", "https://localhost",
                         "https://example.cognitiveservices.azure.com@evil.invalid",
                         "https://example.cognitiveservices.azure.com/?secret=x"):
            with self.subTest(endpoint=endpoint), self.assertRaises(runner.Blocked):
                runner.valid_endpoint(endpoint)

    def test_cross_origin_poll_does_not_receive_credential(self):
        with patch.object(runner, "request", return_value=(202, {
            "Operation-Location": "https://evil.invalid/result"
        }, None)) as req:
            with self.assertRaises(runner.Blocked):
                runner.analyze("https://example.cognitiveservices.azure.com",
                               {"Authorization": "Bearer placeholder"}, b"%PDF-demo")
            self.assertEqual(req.call_count, 1)

    def test_accepted_request_polls_until_succeeded(self):
        endpoint = "https://example.cognitiveservices.azure.com"
        with patch.object(runner, "request", side_effect=[
            (202, {"Operation-Location": endpoint + "/documentintelligence/result"}, None),
            (200, {}, {"status": "running"}),
            (200, {}, {"status": "succeeded", "analyzeResult": {}}),
        ]), patch.object(runner.time, "sleep"):
            self.assertEqual(runner.analyze(endpoint, {}, b"%PDF-demo")["status"],
                             "succeeded")


class WorkbookTests(unittest.TestCase):
    def test_named_sheet_inline_strings_and_iso_dates(self):
        # Temporary files stay within the workspace, never in the parent materials.
        temporary_root = runner.ROOT / "private" / "test-temp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        headers = {"A": "Test-ID", "C": "Dateiname", "E": "Lieferant (Soll)",
                   "F": "Rechnungsnummer (Soll)", "G": "Rechnungsdatum (Soll)",
                   "H": "Fälligkeit (Soll)", "I": "Netto EUR", "J": "USt EUR",
                   "K": "Brutto ausgewiesen EUR"}
        values = {"A": "CASE", "C": "example.pdf", "E": "Example Supplier",
                  "F": "DEMO-001", "G": "01.01.2026", "H": "31.01.2026",
                  "I": "100", "J": "19", "K": "119"}
        def row(number, cells):
            return '<row>' + ''.join(
                f'<c r="{c}{number}" t="inlineStr"><is><t>{v}</t></is></c>'
                for c, v in cells.items()) + '</row>'
        with tempfile.TemporaryDirectory(dir=temporary_root) as temporary:
            path = Path(temporary) / "example.xlsx"
            with zipfile.ZipFile(path, "w") as book:
                book.writestr("xl/workbook.xml", '<workbook xmlns="' + runner.NS["m"] +
                              '" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                              '<sheets><sheet name="Ground Truth" r:id="r2"/></sheets></workbook>')
                book.writestr("xl/_rels/workbook.xml.rels", '<Relationships>'
                              '<Relationship Id="r2" Target="worksheets/sheet2.xml"/></Relationships>')
                book.writestr("xl/worksheets/sheet2.xml", '<worksheet xmlns="' + runner.NS["m"] +
                              '"><sheetData>' + row(1, headers) + row(2, values) + '</sheetData></worksheet>')
            filename, expected = runner.ground_truth(path, "CASE")
            self.assertEqual(filename, "example.pdf")
            self.assertEqual(expected["InvoiceDate"], "2026-01-01")
            self.assertEqual(expected["DueDate"], "2026-01-31")
            self.assertEqual(expected["InvoiceTotal"], "119")
            with self.assertRaisesRegex(runner.Blocked, "ground_truth_test_id_not_unique"):
                runner.ground_truth(path, "MISSING")


if __name__ == "__main__":
    unittest.main()
