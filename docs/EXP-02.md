# EXP-02: source-grounded hosted refinement

## Scope

Compare the existing DI invoice baseline with one source-grounded GPT-5 mini refinement request. Use an already provisioned Azure deployment only. No local LLM, downloads, installs, new deployments, resource modifications, or DI resubmissions are needed. Inference is potentially billable; provisioning does not establish free usage or data-plane access.

The user authorized one small attempted inference, with at most 1,024 completion tokens including reasoning and no retries. The runner additionally bounds source text to 12,000 characters and uses minimal reasoning effort. This is a token boundary, not a guaranteed monetary cost. A failed or timed-out HTTP request still consumes this single-attempt authorization because service-side work cannot be ruled out.

## Request and evaluation separation

`scripts/refine_invoice.py` loads only `analyzeResult.content` from a saved successful DI response into the model request. It does not feed original DI field predictions, comparison reports, workbook values, or private resource metadata to the model. The prompt asks for seven invoice fields, source quotations, null for uncertainty, ISO dates, and decimal amounts. Strict JSON Schema constrains the output structure, not its factual correctness.

The saved invoice was already examined during development. This is an exploratory comparison, not a blinded independent test set or evidence of general improvement. Ground Truth is withheld from inference and loaded only after the model response for evaluation.

Local checks require source quotations to occur in the DI text and support the normalized returned values. Missing fields remain missing. Grounding does not prove correct semantic assignment. No model self-reported confidence or fixed acceptance threshold is used; field importance and review policies remain open.

The original DI response, Ground Truth, and EXP-01 mismatch are preserved. Results distinguish inference success, local grounding validation, baseline match count, and refined match count. A response can be schema-valid or grounded and still contain wrong field assignments.

## Prerequisites and authentication

Use existing Python 3.10+ and Azure CLI. No additional Python dependencies are required. Authenticate privately using the workspace-local Azure CLI configuration described in EXP-01. A private inventory must identify exactly one provisioned GPT-5 mini deployment. The runner rechecks the deployment before inference. It supports the earlier private inventory helper's array wrapper.

For key-enabled resources, an existing resource key is read through Azure CLI directly into memory; it is never printed or saved. Alternatively supply `AZURE_OPENAI_API_KEY` through an approved environment/secret mechanism. If key authentication is disabled, the runner attempts an Entra token. No roles, keys, or account settings are changed. Management-plane access alone does not establish inference access.

Only validated Azure HTTPS hosts are accepted. Redirects are refused. The code uses one standard-library HTTP POST with no SDK retry policy. Authentication and HTTP error details are represented by safe blocker codes rather than raw bodies, URLs, headers, or token values.

## Run once

From the repository root, fill the placeholders privately:

```powershell
python -B scripts/refine_invoice.py --inventory '<private-inventory-json>' --source-run '<private-successful-di-run-folder>' --ground-truth '<private-workbook-path>' --single-approved-call
```

The source run must contain `response.private.json` and the original `report.private.json`, including its test ID and workbook hash. The original workbook must remain unchanged. The private inventory format is an object with an `accounts` array; each account provides `name`, `group`, and `deployments`, with deployment `name`, `model`, and `state` fields. Keep all real account/deployment selections out of public tracking.

The global guard `private/exp02/single-call-consumed.private.json` is atomically created just before the HTTP request. CLI/input failures before that point do not consume the allowance. Once created, the guard remains even after errors or timeouts. Do not delete it or rerun elsewhere to bypass the approved call limit. A further attempt needs a new explicit decision.

## Evidence and tests

Each invocation saves a unique ignored `private/exp02/<run-id>/` folder with the exact credential-free request, run report, and, if available, model completion and parsed fields. The report records model usage when returned, output limit, timestamps, input hash, blockers, and comparisons. Private completion metadata and prompts must be reviewed separately before any academic disclosure or publication. No credentials or HTTP headers are saved.

Exit codes: `0` = refined fields match Ground Truth; `1` = comparison completed with mismatches; `2` = blocked, ungrounded, refused, truncated, or invalid output. Incomplete output is not retried. No model result is automatically promoted into a production record.

Run `python -B -m unittest discover -s tests -v` for offline checks of both experiments. These tests use invented fixtures and mocked behavior; they do not consume the authorized inference call. Actual live improvement remains unverified until a saved model result has been inspected.

API references: [Microsoft structured outputs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs), [Chat Completions reference](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat).
