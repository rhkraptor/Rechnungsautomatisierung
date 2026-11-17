# EXP-01: invoice extraction

## Scope and prerequisites

Use Python 3.10+ and an existing Azure CLI installation. No Python packages are required. The runner reads a synthetic PDF and an Open XML workbook, discovers an explicitly named existing Document Intelligence resource, verifies kind `FormRecognizer` and tier `F0`, and submits page 1 to `prebuilt-invoice` with locale `de-DE` and REST API `2024-11-30`.

No resource creation, resource updates, key listing, key rotation, SharePoint, or Outlook operations are performed. Each invocation makes at most one analysis submission; rerunning a completed invocation creates another analysis and consumes service quota. Do not submit real invoices. This experiment covers one page, not arbitrary multipage invoices.

## Local authentication

The runner isolates Azure CLI authentication and caches under ignored `private/azure/` to avoid writing user-level configuration. It does not copy authentication files or silently initiate interactive login. Authenticate once in your own PowerShell terminal, from the repository root:

```powershell
$env:AZURE_CONFIG_DIR = Join-Path (Get-Location) 'private/azure'
$env:AZURE_CORE_COLLECT_TELEMETRY = 'false'
az login --use-device-code --output none
```

Complete device authentication privately. Do not paste device codes or sign-in output into public issues or transcripts. Select the authorized subscription privately if necessary. Existing authentication in a different CLI configuration directory is not reused.

By default, the runner obtains a short-lived Cognitive Services token through Azure CLI and retains it only in memory. Resource discovery needs read access and extraction needs appropriate data-plane authorization. A successful login alone does not establish either permission.

If key authentication is explicitly permitted instead, supply `AZURE_DOCUMENT_INTELLIGENCE_KEY` through an approved secret mechanism into the process environment, never as a command-line argument or a committed file. Discovery still requires CLI authentication and read permission. `.env` files are not loaded automatically. Do not print the environment or authentication responses.

## Run

Supply real local paths and resource selections privately; placeholders below are not runnable values:

```powershell
python -B scripts/extract_invoice.py --input '<synthetic-pdf-path>' --ground-truth '<workbook-path>' --test-id '<test-id>' --resource-name '<existing-resource>' --resource-group '<existing-group>' --synthetic-only
```

Resource name/group may alternatively come from `AZURE_DI_RESOURCE_NAME` and `AZURE_DI_RESOURCE_GROUP`. The named workbook sheet must be `Ground Truth` with the expected column headers; exactly one matching test ID and matching PDF filename are required. Inputs are read-only. The flag confirms synthetic-only use; it cannot automatically prove provenance.

The service endpoint is obtained from resource discovery, not from a user-supplied URL. Only public Azure Cognitive Services HTTPS endpoints are accepted. Redirects are refused; polling must remain on the same origin and in the Document Intelligence API path. The runner does not print URLs, credential values, raw CLI errors, or response bodies. It captures CLI authentication output in memory and records only predefined blocker codes. It does not fall back to a paid tier or create resources.

## Comparison and evidence

The seven compared fields are vendor name, invoice ID, invoice date, due date, subtotal, total tax, and invoice total. Dates from the workbook are normalized to ISO format; text uses Unicode NFC and whitespace normalization with case preserved. Monetary comparisons use exact decimal equality. A returned non-EUR currency fails; absent currency metadata does not independently confirm EUR. Confidence is recorded without inventing an acceptance threshold. Missing typed values fail even when raw OCR content is present; values are never filled from expected data. Exactly one returned invoice is required.

Each invocation creates a unique ignored `private/exp01/<run-id>/report.private.json` containing timestamps, input/workbook hashes, expected values, stage, comparison or blocker, and elapsed time. A successful service analysis also saves `response.private.json` for private inspection. No authorization headers or tokens are saved. The process prints only a generic status, blocker code, and relative evidence location. If submission was attempted but no terminal result was received, inspect the run before resubmitting; timeout does not prove the service did no work.

Exit codes: `0` = all seven comparisons match; `1` = completed comparison with differences; `2` = blocked or invalid input/response. An analysis can succeed while comparison is blocked or fails; inspect `extraction_succeeded` separately. The runner never automatically updates public documentation or commits results. Publish only reviewed, sanitized milestones.

## API references

- [Microsoft: analyze document from stream](https://learn.microsoft.com/en-us/rest/api/aiservices/document-models/analyze-document-from-stream?view=rest-aiservices-v4.0%20(2024-11-30))
- [Microsoft: get analysis result](https://learn.microsoft.com/en-us/rest/api/aiservices/document-models/get-analyze-result?view=rest-aiservices-v4.0%20(2024-11-30))

The documented API accepts binary input with asynchronous polling. The specific tenant, resource, credentials, connectivity, and extraction accuracy must still be tested; documentation is not execution evidence.
