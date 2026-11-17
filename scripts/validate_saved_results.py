"""Offline replay of saved DI/refined results under the current local review policy."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid

from extract_invoice import Blocked, ROOT, write_json
from refine_invoice import FIELDS, build_payload, validate_fields

sys.path.insert(0, str(ROOT / "src"))
from invoice_validation import POLICY_VERSION, evaluate_records


def flatten(response):
    documents = response.get("analyzeResult", {}).get("documents", [])
    if response.get("status") != "succeeded" or len(documents) != 1:
        raise Blocked("expected_one_successful_invoice_response")
    fields = documents[0].get("fields", {})
    values = {}
    for name in FIELDS:
        field = fields.get(name) or {}
        if name in ("SubTotal", "TotalTax", "InvoiceTotal"):
            values[name] = (field.get("valueCurrency") or {}).get("amount", field.get("valueNumber"))
        elif name.endswith("Date"):
            values[name] = field.get("valueDate")
        else:
            values[name] = field.get("valueString")
    return values


def load_record(record_id, di_folder, refinement_folder):
    source_path = di_folder / "response.private.json"
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    refined_bytes = (refinement_folder / "refined.private.json").read_bytes()
    refined = json.loads(refined_bytes)
    request = json.loads((refinement_folder / "request.private.json").read_text(encoding="utf-8"))
    content = source["analyzeResult"]["content"]
    request_matches = request == build_payload(content, request["model"])
    reasons = []
    try:
        if not request_matches:
            raise Blocked("saved_request_differs_from_source_only_builder")
        typed = validate_fields(refined, content)
        refined_values = flatten(typed)
        grounded = True
    except (Blocked, ValueError, TypeError, KeyError):
        # Unsupported candidates are preserved in original evidence, not treated as valid values.
        refined_values = {name: None for name in FIELDS}
        grounded = False
        reasons.append("saved_source_grounding_or_request_validation_failed")
    return {"record_id": record_id, "raw": flatten(source), "refined": refined_values,
            "source_grounding_validated": grounded,
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "refined_sha256": hashlib.sha256(refined_bytes).hexdigest(),
            "evidence_issues": reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-di-run", type=Path, required=True)
    parser.add_argument("--development-refinement-run", type=Path, required=True)
    parser.add_argument("--batch-run", type=Path, required=True)
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    folder = ROOT / "private" / "validation" / run_id
    folder.mkdir(parents=True)
    report = {"policy_version": POLICY_VERSION, "run_id": run_id, "status": "blocked",
              "cloud_calls": 0, "ground_truth_used": False}
    try:
        records = [load_record("T01", args.development_di_run, args.development_refinement_run)]
        for test_id in ("T02", "T03", "T04", "T05"):
            records.append(load_record(test_id, args.batch_run / test_id, args.batch_run / test_id))
        results = evaluate_records(records)
        write_json(folder / "records.private.json", records)
        write_json(folder / "manual-review-queue.private.json", [
            {"decision": result, "raw": record["raw"], "refined": record["refined"],
             "tester_resolution": None}
            for record, result in zip(records, results) if result["status"] == "review_required"
        ])
        report.update(status="completed", results=results, records=len(records),
                      review_required=sum(r["status"] == "review_required" for r in results),
                      checks_passed=sum(r["status"] == "checks_passed" for r in results),
                      automatic_approvals=0)
    except (Blocked, OSError, ValueError, KeyError, TypeError, IndexError):
        report["blocker"] = "saved_input_or_policy_validation_failed"
    write_json(folder / "report.private.json", report)
    print("Local validation:", report["status"])
    if report["status"] == "completed":
        print("Records:", report["records"], "Review required:", report["review_required"],
              "Checks passed:", report["checks_passed"])
    print("Private evidence:", folder.relative_to(ROOT).as_posix())
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
