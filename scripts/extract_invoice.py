"""EXP-01: synthetic PDF extraction and workbook comparison; standard library only."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
API_VERSION = "2024-11-30"
MODEL = "prebuilt-invoice"
MONEY = {"SubTotal", "TotalTax", "InvoiceTotal"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class Blocked(Exception):
    """Only safe, predefined messages: never include raw CLI/HTTP errors."""


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ground_truth(path, test_id):
    """Read expected values directly, resolving sheet name rather than sheet order."""
    with zipfile.ZipFile(path) as book:
        strings = []
        if "xl/sharedStrings.xml" in book.namelist():
            strings = ["".join(e.itertext()) for e in
                       ET.fromstring(book.read("xl/sharedStrings.xml"))]
        sheets = ET.fromstring(book.read("xl/workbook.xml"))
        sheet = next(s for s in sheets.findall("m:sheets/m:sheet", NS)
                     if s.get("name") == "Ground Truth")
        relation_id = sheet.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        relations = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in relations if r.get("Id") == relation_id)
        sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
        rows = []
        for row in ET.fromstring(book.read(sheet_path)).findall("m:sheetData/m:row", NS):
            values = {}
            for cell in row:
                value = cell.find("m:v", NS)
                text = value.text if value is not None else "".join(
                    cell.find("m:is", NS).itertext()) if cell.find("m:is", NS) is not None else ""
                if cell.get("t") == "s":
                    text = strings[int(text)]
                values[re.sub(r"\d", "", cell.get("r"))] = text
            rows.append(values)
    required = {
        "A": "Test-ID", "C": "Dateiname", "E": "Lieferant (Soll)",
        "F": "Rechnungsnummer (Soll)", "G": "Rechnungsdatum (Soll)",
        "H": "Fälligkeit (Soll)", "I": "Netto EUR", "J": "USt EUR",
        "K": "Brutto ausgewiesen EUR",
    }
    if not rows or any(rows[0].get(c) != name for c, name in required.items()):
        raise Blocked("ground_truth_schema_mismatch")
    matches = [r for r in rows[1:] if r.get("A") == test_id]
    if len(matches) != 1:
        raise Blocked("ground_truth_test_id_not_unique")
    row = matches[0]
    expected = {name: row[column] for name, column in {
        "VendorName": "E", "InvoiceId": "F", "InvoiceDate": "G", "DueDate": "H",
        "SubTotal": "I", "TotalTax": "J", "InvoiceTotal": "K",
    }.items()}
    for name in ("InvoiceDate", "DueDate"):
        expected[name] = datetime.strptime(expected[name], "%d.%m.%Y").date().isoformat()
    return row["C"], expected


def compare(response, expected):
    if response.get("status") != "succeeded":
        raise Blocked("analysis_not_succeeded")
    documents = response.get("analyzeResult", {}).get("documents", [])
    if len(documents) != 1:
        raise Blocked("expected_exactly_one_invoice")
    fields = documents[0].get("fields", {})
    rows = []
    for name, wanted in expected.items():
        field = fields.get(name) or {}
        currency = field.get("valueCurrency") or {}
        if name in MONEY:
            actual = currency.get("amount", field.get("valueNumber"))
            code = currency.get("currencyCode")
            try:
                # No undocumented tolerance: exact decimal agreement for these synthetic totals.
                match = actual is not None and Decimal(str(actual)) == Decimal(wanted)
                match = match and code in (None, "EUR")
            except InvalidOperation:
                match = False
        else:
            actual = field.get("valueDate") if name.endswith("Date") else field.get("valueString")
            normalize = lambda s: " ".join(unicodedata.normalize("NFC", s).split())
            match = isinstance(actual, str) and normalize(actual) == normalize(wanted)
            code = None
        rows.append({"field": name, "expected": wanted, "actual": actual,
                     "currency": code, "confidence": field.get("confidence"),
                     "match": bool(match)})
    return rows


def cli(args):
    executable = shutil.which("az")
    if not executable:
        raise Blocked("azure_cli_not_installed")
    # Never write to user-level CLI caches or copy user authentication files.
    config = ROOT / "private" / "azure"
    config.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, AZURE_CONFIG_DIR=str(config),
               AZURE_CORE_COLLECT_TELEMETRY="false", AZURE_CORE_ONLY_SHOW_ERRORS="true")
    try:
        result = subprocess.run(
            [executable, *args, "--output", "json", "--only-show-errors"],
            env=env, capture_output=True, text=True, timeout=45,
        )
    except subprocess.TimeoutExpired:
        raise Blocked("azure_cli_timeout") from None
    if result.returncode:
        error = result.stderr.lower()
        if "permission denied" in error or "access is denied" in error:
            reason = "azure_cli_profile_permission_denied"
        elif "az login" in error or "please run" in error:
            reason = "azure_cli_login_required_in_private_config"
        elif any(s in error for s in ("connection", "name resolution", "proxy", "network")):
            reason = "azure_cli_network_unavailable"
        else:
            reason = "azure_cli_command_failed"
        raise Blocked(reason)
    return json.loads(result.stdout)


def valid_endpoint(endpoint):
    parts = urlsplit(endpoint)
    if (parts.scheme != "https" or parts.username or parts.password
            or parts.port not in (None, 443) or parts.query or parts.fragment
            or parts.path not in ("", "/")
            or not re.fullmatch(r"[a-z0-9-]+\.(cognitiveservices\.azure\.com|api\.cognitive\.microsoft\.com)",
                                parts.hostname or "")):
        raise Blocked("untrusted_service_endpoint")
    return endpoint.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("http_redirect_refused")


def request(url, headers, data=None):
    try:
        with build_opener(NoRedirect()).open(Request(url, data=data, headers=headers),
                                             timeout=30) as response:
            payload = response.read()
            return response.status, response.headers, json.loads(payload) if payload else None
    except HTTPError as error:
        # Do not log bodies, URLs, headers, or raw errors; they may expose metadata.
        raise Blocked("http_status_" + str(error.code)) from None
    except (URLError, TimeoutError, OSError):
        raise Blocked("extraction_network_or_tls_unavailable") from None


def analyze(endpoint, headers, pdf):
    endpoint = valid_endpoint(endpoint)
    url = endpoint + "/documentintelligence/documentModels/" + MODEL + ":analyze"
    url += "?api-version=" + API_VERSION + "&locale=de-DE&pages=1"
    status, response_headers, _ = request(url, dict(headers, **{"Content-Type": "application/pdf"}), pdf)
    if status != 202:
        raise Blocked("analysis_not_accepted")
    operation = response_headers.get("Operation-Location")
    origin = urlsplit(endpoint)
    poll = urlsplit(operation or "")
    if (not operation or (poll.scheme, poll.netloc) != (origin.scheme, origin.netloc)
            or not poll.path.startswith("/documentintelligence/") or poll.fragment):
        raise Blocked("untrusted_operation_location")
    deadline = time.monotonic() + 120
    delay = response_headers.get("Retry-After", "2")
    while time.monotonic() < deadline:
        try:
            wait = max(1, min(float(delay), 10))
        except (TypeError, ValueError):
            wait = 2
        time.sleep(wait)
        _, response_headers, result = request(operation, headers)
        if not isinstance(result, dict):
            raise Blocked("invalid_poll_response")
        if result.get("status") == "succeeded":
            return result
        if result.get("status") not in ("running", "notStarted"):
            raise Blocked("analysis_service_failed")
        delay = response_headers.get("Retry-After", "2")
    raise Blocked("analysis_poll_timeout_no_automatic_resubmit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--test-id", default="T01")
    parser.add_argument("--resource-name", default=os.getenv("AZURE_DI_RESOURCE_NAME"))
    parser.add_argument("--resource-group", default=os.getenv("AZURE_DI_RESOURCE_GROUP"))
    parser.add_argument("--synthetic-only", action="store_true", required=True,
                        help="Confirm that the supplied invoice is synthetic")
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    folder = ROOT / "private" / "exp01" / run_id
    folder.mkdir(parents=True)
    report = {"experiment": "EXP-01", "test_id": args.test_id, "run_id": run_id,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "api_version": API_VERSION, "model": MODEL, "pages": "1", "locale": "de-DE",
              "status": "blocked", "stage": "input_validation", "comparison": None,
              "extraction_succeeded": False, "submission_attempted": False}
    started = time.monotonic()
    exit_code = 2
    try:
        filename, expected = ground_truth(args.ground_truth, args.test_id)
        if filename != args.input.name:
            raise Blocked("input_filename_differs_from_workbook")
        pdf = args.input.read_bytes()
        if not pdf.startswith(b"%PDF-"):
            raise Blocked("input_is_not_pdf")
        report.update(expected=expected, input_sha256=hashlib.sha256(pdf).hexdigest(),
                      workbook_sha256=hashlib.sha256(args.ground_truth.read_bytes()).hexdigest())
        if not args.resource_name or not args.resource_group:
            raise Blocked("existing_resource_name_and_group_required")
        report["stage"] = "resource_discovery"
        resource = cli(["cognitiveservices", "account", "show", "--name", args.resource_name,
                        "--resource-group", args.resource_group, "--query",
                        "{endpoint:properties.endpoint,kind:kind,tier:sku.name}"])
        if resource.get("tier") != "F0" or resource.get("kind") != "FormRecognizer":
            raise Blocked("resource_must_be_existing_form_recognizer_f0")
        endpoint = valid_endpoint(resource["endpoint"])
        report["resource"] = {"name": args.resource_name, "group": args.resource_group,
                              "kind": resource["kind"], "tier": resource["tier"]}
        report["stage"] = "authentication"
        key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        if key and (key.startswith("<") or key.isspace()):
            raise Blocked("credential_placeholder_not_configured")
        if key:
            headers = {"Ocp-Apim-Subscription-Key": key}
            report["authentication"] = "environment_key"
        else:
            credential = cli(["account", "get-access-token", "--resource",
                              "https://cognitiveservices.azure.com/", "--query", "accessToken"])
            if not isinstance(credential, str) or not credential:
                raise Blocked("access_token_unavailable")
            headers = {"Authorization": "Bearer " + credential}
            report["authentication"] = "azure_cli_entra_token"
        report["stage"] = "extraction"
        report["submission_attempted"] = True
        response = analyze(endpoint, headers, pdf)
        report["extraction_succeeded"] = True
        # Response body only; never persist authentication or HTTP headers.
        write_json(folder / "response.private.json", response)
        report["stage"] = "comparison"
        report["comparison"] = compare(response, expected)
        report["status"] = "passed" if all(r["match"] for r in report["comparison"]) else "mismatch"
        exit_code = 0 if report["status"] == "passed" else 1
    except Blocked as error:
        report["blocker"] = str(error)
    except (OSError, ValueError, KeyError, StopIteration, zipfile.BadZipFile, ET.ParseError):
        report["blocker"] = "local_input_or_response_invalid"
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(folder / "report.private.json", report)
    print("EXP-01 status:", report["status"])
    if "blocker" in report:
        print("Blocker:", report["blocker"])
    print("Private evidence:", folder.relative_to(ROOT).as_posix())
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
