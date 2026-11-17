"""Invented offline fixtures for bounded batch evaluation."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evaluate_invoice_batch as batch


class BatchTests(unittest.TestCase):
    def test_started_batch_cannot_spend_again(self):
        root = batch.ROOT / "private" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            budget = Path(folder) / "private" / "exp03" / "budget"
            budget.mkdir(parents=True)
            (budget / "batch-started.private.json").write_text('{}')
            argv = ['batch', '--inventory', 'unused', '--input-dir', 'unused',
                    '--ground-truth', 'unused', '--di-resource-name', 'example-resource',
                    '--di-resource-group', 'example-group', '--approved-four-case-batch', '--synthetic-only']
            with patch.object(batch, 'ROOT', Path(folder)), patch.object(sys, 'argv', argv), \
                    patch.object(batch, 'discover') as discover, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(batch.main(), 2)
                discover.assert_not_called()

    def test_failed_di_consumes_one_attempt_without_refinement(self):
        root = batch.ROOT / "private" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            case = {"test_id": "T02", "input_sha256": "example-hash", "pdf": b"%PDF-demo", "expected": {}}
            services = ('https://example.cognitiveservices.azure.com', {},
                        'https://example.openai.azure.com', {}, 'example-deployment')
            with patch.object(batch, 'analyze', side_effect=batch.Blocked('http_status_429')) as analyze, \
                    patch.object(batch, 'refine_once') as refine:
                report = batch.evaluate_case(case, services, Path(folder), 'run', Path(folder))
                self.assertEqual(report['status'], 'blocked')
                self.assertEqual(analyze.call_count, 1)
                refine.assert_not_called()
                self.assertTrue((Path(folder)/'T02-di.private.json').is_file())

    def response(self, invoice_id=None):
        fields = {} if invoice_id is None else {"InvoiceId": {"valueString": invoice_id}}
        return {"status": "succeeded", "analyzeResult": {"documents": [{"fields": fields}]}}

    def test_correct_absence_matches_observation_not_business_acceptance(self):
        rows = batch.evaluate_observations(self.response(), {"InvoiceId": "NICHT VORHANDEN"})
        self.assertTrue(rows[0]["match"])
        self.assertEqual(rows[0]["observation"], "correct_absence")
        self.assertIsNone(rows[0]["expected"])
        self.assertEqual(batch.review_reasons(rows, rows), ["missing_InvoiceId"])

    def test_invented_number_does_not_match_expected_absence(self):
        rows = batch.evaluate_observations(self.response("DEMO-123"), {"InvoiceId": "NICHT VORHANDEN"})
        self.assertFalse(rows[0]["match"])
        self.assertEqual(rows[0]["observation"], "unexpected_value")

    def test_missing_expected_number_is_not_correct_absence(self):
        rows = batch.evaluate_observations(self.response(), {"InvoiceId": "DEMO-123"})
        self.assertFalse(rows[0]["match"])
        self.assertEqual(rows[0]["observation"], "missing_value")

    def test_disagreement_requires_review_even_when_refinement_matches(self):
        raw = batch.evaluate_observations(self.response("WRONG"), {"InvoiceId": "DEMO-123"})
        refined = batch.evaluate_observations(self.response("DEMO-123"), {"InvoiceId": "DEMO-123"})
        self.assertIn("raw_refined_disagree_InvoiceId", batch.review_reasons(raw, refined))

    def test_marker_is_case_and_service_specific_and_not_reusable(self):
        root = batch.ROOT / "private" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            budget = Path(folder)
            batch.claim_attempt(budget, "T02", "di", "first")
            batch.claim_attempt(budget, "T02", "llm", "first")
            with self.assertRaises(batch.Blocked):
                batch.claim_attempt(budget, "T02", "di", "second")
            with self.assertRaises(batch.Blocked):
                batch.claim_attempt(budget, "T01", "llm", "second")
            with self.assertRaises(batch.Blocked):
                batch.claim_attempt(budget, "T05", "unknown-service", "second")
            self.assertEqual(len(list(budget.glob('*.json'))), 2)

    def test_failed_inference_consumes_attempt_and_is_not_retried(self):
        root = batch.ROOT / "private" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            with patch.object(batch, "request", side_effect=batch.Blocked("http_status_429")) as req:
                with self.assertRaises(batch.Blocked):
                    batch.refine_once("https://example.openai.azure.com", {},
                                      "Example Supplier", "example-deployment", Path(folder),
                                      "T02", "run", Path(folder))
                self.assertEqual(req.call_count, 1)
                self.assertTrue((Path(folder)/'T02-llm.private.json').is_file())

    def test_comparison_counts_keep_absence_distinct(self):
        rows = [{"match": True, "observation": "correct_absence"},
                {"match": True, "observation": "value_match"},
                {"match": False, "observation": "value_mismatch"}]
        self.assertEqual(batch.score(rows), {"matches": 2, "fields": 3,
                                           "value_matches": 1, "correct_absences": 1})

    def test_header_equality_is_not_an_automatic_duplicate_decision(self):
        rows = [{"field": "InvoiceId", "actual": "DEMO-123"}]
        result = batch.duplicate_observation({"T03": {"refined_comparison": rows},
                                              "T04": {"refined_comparison": rows}})
        self.assertTrue(result["matching_available_header_values"])
        self.assertEqual(result["workflow_duplicate_decision"], "not_defined")


if __name__ == '__main__':
    unittest.main()
