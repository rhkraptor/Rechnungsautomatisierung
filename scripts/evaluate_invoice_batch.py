"""EXP-03: bounded four-case DI/LLM evaluation; no workflow acceptance decisions."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from extract_invoice import Blocked, ROOT, MONEY, analyze, cli, compare, ground_truth, valid_endpoint, write_json
from refine_invoice import build_payload, request, select_deployment, validate_endpoint, validate_fields

CASES = ("T02", "T03", "T04", "T05")


def evaluate_observations(response, expected):
    rows = compare(response, expected)
    for row in rows:
        actual = row["actual"]
        absent = actual is None or isinstance(actual, str) and not actual.strip()
        expected_absent = row["field"] == "InvoiceId" and row["expected"] == "NICHT VORHANDEN"
        if expected_absent:
            row["expected"] = None
            row["match"] = absent
            row["observation"] = "correct_absence" if absent else "unexpected_value"
        elif absent:
            row["observation"] = "missing_value"
        else:
            row["observation"] = "value_match" if row["match"] else "value_mismatch"
    return rows


def score(rows):
    return {"matches": sum(row["match"] for row in rows), "fields": len(rows),
            "value_matches": sum(row["observation"] == "value_match" for row in rows),
            "correct_absences": sum(row["observation"] == "correct_absence" for row in rows)}


def comparable(row):
    value = row["actual"]
    if value is None:
        return None
    if row["field"] in MONEY:
        return Decimal(str(value))
    return " ".join(str(value).split())


def review_reasons(raw, refined):
    reasons = []
    by_field = {row["field"]: row for row in raw}
    for row in refined:
        if row["actual"] is None or isinstance(row["actual"], str) and not row["actual"].strip():
            reasons.append("missing_" + row["field"])
        if comparable(row) != comparable(by_field[row["field"]]):
            reasons.append("raw_refined_disagree_" + row["field"])
    return reasons


def duplicate_observation(reports):
    result = {"workflow_duplicate_decision": "not_defined",
              "matching_available_header_values": None, "compared_fields": 0}
    first = reports.get("T03", {}).get("refined_comparison")
    second = reports.get("T04", {}).get("refined_comparison")
    if first and second:
        a = {row["field"]: comparable(row) for row in first}
        b = {row["field"]: comparable(row) for row in second}
        available = {name for name in a.keys() & b.keys() if a[name] is not None and b[name] is not None}
        result["compared_fields"] = len(available)
        result["matching_available_header_values"] = bool(available) and all(a[k] == b[k] for k in available)
    return result


def claim_attempt(budget, test_id, service, run_id):
    if test_id not in CASES or service not in ("di", "llm"):
        raise Blocked("attempt_outside_approved_four_case_budget")
    try:
        with (budget / (test_id + "-" + service + ".private.json")).open("x", encoding="utf-8") as stream:
            json.dump({"run_id": run_id, "test_id": test_id, "service": service,
                       "completion_token_cap": 1024 if service == "llm" else None}, stream)
    except FileExistsError:
        raise Blocked("case_service_attempt_already_consumed") from None


def refine_once(endpoint, headers, content, deployment, budget, test_id, run_id, folder):
    payload = build_payload(content, deployment)
    write_json(folder / "request.private.json", payload)
    claim_attempt(budget, test_id, "llm", run_id)
    # Shared HTTP transport refuses redirects; no SDK or automatic HTTP retries.
    _, _, completion = request(endpoint + "/openai/v1/chat/completions", headers,
                                json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    write_json(folder / "completion.private.json", completion)
    choice = completion["choices"][0]
    if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
        raise Blocked("model_output_incomplete_or_refused_no_retry")
    fields = json.loads(choice["message"]["content"])
    write_json(folder / "refined.private.json", fields)
    typed = validate_fields(fields, content)
    return typed, completion.get("usage"), completion.get("model")


def credentials(name, group, resource, env_name, key_header):
    key = os.getenv(env_name)
    if not key and not resource.get("localAuthDisabled"):
        key = cli(["cognitiveservices", "account", "keys", "list", "--name", name,
                   "--resource-group", group, "--query", "key1"])
    if key:
        if not isinstance(key, str) or key.startswith("<") or not key.strip():
            raise Blocked("invalid_or_placeholder_credential")
        return {key_header: key}
    token = cli(["account", "get-access-token", "--resource",
                 "https://cognitiveservices.azure.com/", "--query", "accessToken"])
    if not isinstance(token, str) or not token:
        raise Blocked("access_token_unavailable")
    return {"Authorization": "Bearer " + token}


def prepare_cases(input_dir, workbook):
    cases = []
    for test_id in CASES:
        filename, expected = ground_truth(workbook, test_id)
        if Path(filename).name != filename:
            raise Blocked("workbook_filename_must_be_basename")
        pdf = (input_dir / filename).read_bytes()
        if not pdf.startswith(b"%PDF-"):
            raise Blocked("input_is_not_pdf")
        cases.append({"test_id": test_id, "filename": filename, "pdf": pdf,
                      "input_sha256": hashlib.sha256(pdf).hexdigest(), "expected": expected})
    return cases


def discover(inventory, di_name, di_group):
    projection = "{endpoint:properties.endpoint,localAuthDisabled:properties.disableLocalAuth,kind:kind,tier:sku.name}"
    di = cli(["cognitiveservices", "account", "show", "--name", di_name,
              "--resource-group", di_group, "--query", projection])
    if di.get("kind") != "FormRecognizer" or di.get("tier") != "F0":
        raise Blocked("di_must_be_existing_form_recognizer_f0")
    di_endpoint = valid_endpoint(di["endpoint"])
    account, deployment = select_deployment(inventory)
    current = cli(["cognitiveservices", "account", "deployment", "show", "--name", account["name"],
                   "--resource-group", account["group"], "--deployment-name", deployment["name"],
                   "--query", "{model:properties.model.name,state:properties.provisioningState}"])
    if current.get("model") != "gpt-5-mini" or current.get("state") != "Succeeded":
        raise Blocked("existing_llm_deployment_changed_or_unavailable")
    llm = cli(["cognitiveservices", "account", "show", "--name", account["name"],
               "--resource-group", account["group"], "--query", projection])
    llm_endpoint = validate_endpoint(llm["endpoint"])
    di_headers = credentials(di_name, di_group, di, "AZURE_DOCUMENT_INTELLIGENCE_KEY",
                             "Ocp-Apim-Subscription-Key")
    llm_headers = credentials(account["name"], account["group"], llm, "AZURE_OPENAI_API_KEY", "api-key")
    llm_headers["Content-Type"] = "application/json"
    return di_endpoint, di_headers, llm_endpoint, llm_headers, deployment["name"]


def evaluate_case(case, services, budget, run_id, folder):
    test_id = case["test_id"]
    di_endpoint, di_headers, llm_endpoint, llm_headers, deployment = services
    report = {"test_id": test_id, "status": "blocked", "stage": "di_submission",
              "input_sha256": case["input_sha256"], "baseline_comparison": None,
              "refined_comparison": None, "workflow_disposition": "review_required_pending_business_rules",
              "di_succeeded": False, "refinement_validated": False, "retry_count": 0}
    started = time.monotonic()
    try:
        claim_attempt(budget, test_id, "di", run_id)
        source = analyze(di_endpoint, di_headers, case["pdf"])
        write_json(folder / "response.private.json", source)
        report["di_succeeded"] = True
        report["stage"] = "baseline_evaluation"
        raw_rows = evaluate_observations(source, case["expected"])
        report["baseline_comparison"] = raw_rows
        report["baseline_score"] = score(raw_rows)
        if test_id == "T05":
            items = source["analyzeResult"]["documents"][0].get("fields", {}).get("Items", {}).get("valueArray")
            report["line_items_observation"] = {
                "expected_fixture_count": 2, "di_items_count": len(items) if isinstance(items, list) else None,
                "individual_item_values_validated": False, "llm_schema_includes_items": False,
            }
        report["stage"] = "refinement_and_source_grounding"
        typed, usage, model = refine_once(llm_endpoint, llm_headers, source["analyzeResult"]["content"],
                                         deployment, budget, test_id, run_id, folder)
        report.update(refinement_validated=True, usage=usage, returned_model=model)
        report["stage"] = "refined_evaluation"
        refined_rows = evaluate_observations(typed, case["expected"])
        report["refined_comparison"] = refined_rows
        report["refined_score"] = score(refined_rows)
        report["field_review_reasons"] = review_reasons(raw_rows, refined_rows)
        report["status"] = "evaluated"
    except Blocked as error:
        report["blocker"] = str(error)
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        report["blocker"] = "invalid_input_or_service_response"
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write_json(folder / "report.private.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--di-resource-name", required=True)
    parser.add_argument("--di-resource-group", required=True)
    parser.add_argument("--approved-four-case-batch", action="store_true", required=True)
    parser.add_argument("--synthetic-only", action="store_true", required=True)
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    folder = ROOT / "private" / "exp03" / run_id
    folder.mkdir(parents=True)
    budget = ROOT / "private" / "exp03" / "budget"
    budget.mkdir(parents=True, exist_ok=True)
    summary = {"experiment": "EXP-03", "run_id": run_id, "status": "blocked",
               "started_utc": datetime.now(timezone.utc).isoformat(), "stage": "input_validation",
               "cases": {}, "max_di_analyses": 4, "max_llm_attempts": 4,
               "completion_cap_per_llm": 1024, "automatic_retries": 0,
               "workflow_policy": "provisional_all_seven_fields_review_missing_or_ambiguous"}
    try:
        if any(budget.glob("*.json")):
            raise Blocked("approved_batch_already_started_no_automatic_resume")
        cases = prepare_cases(args.input_dir, args.ground_truth)
        workbook_hash = hashlib.sha256(args.ground_truth.read_bytes()).hexdigest()
        summary["workbook_sha256"] = workbook_hash
        # Record the frozen prompt/schema, independent of any case or expected values.
        template = build_payload("source-placeholder", "deployment-placeholder")
        summary["prompt_schema_sha256"] = hashlib.sha256(
            json.dumps(template, sort_keys=True).encode("utf-8")).hexdigest()
        inventory = json.loads(args.inventory.read_text(encoding="utf-8-sig"))
        summary["stage"] = "resource_discovery_and_authentication"
        services = discover(inventory, args.di_resource_name, args.di_resource_group)
        summary["stage"] = "batch_guard"
        try:
            with (budget / "batch-started.private.json").open("x", encoding="utf-8") as stream:
                json.dump({"run_id": run_id, "cases": list(CASES), "max_di": 4, "max_llm": 4}, stream)
        except FileExistsError:
            raise Blocked("approved_batch_already_started_no_automatic_resume") from None
        summary["stage"] = "case_evaluation"
        for case in cases:
            case_folder = folder / case["test_id"]
            case_folder.mkdir()
            result = evaluate_case(case, services, budget, run_id, case_folder)
            summary["cases"][case["test_id"]] = result
            write_json(folder / "summary.private.json", summary)
            if result["status"] == "blocked":
                raise Blocked("case_blocked_stopped_batch_inspect_private_evidence")
        if hashlib.sha256(args.ground_truth.read_bytes()).hexdigest() != workbook_hash:
            raise Blocked("workbook_changed_during_batch")
        summary["duplicate_observation"] = duplicate_observation(summary["cases"])
        summary["status"] = "completed"
    except Blocked as error:
        summary["blocker"] = str(error)
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        summary["blocker"] = "invalid_local_input_or_discovery_response"
    finally:
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(folder / "summary.private.json", summary)
    print("EXP-03 status:", summary["status"])
    if "blocker" in summary:
        print("Blocker:", summary["blocker"])
    print("Private evidence:", folder.relative_to(ROOT).as_posix())
    return 0 if summary["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
