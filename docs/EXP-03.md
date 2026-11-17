# EXP-03: bounded evaluation on four additional synthetic files

## Approved scope

Evaluate T02 (missing invoice number), T03 (original), T04 (duplicate contents), and T05 (two positions), using existing resources only. The maximum authorized attempts are four DI analyses and four GPT-5 mini requests, one of each per case. Each LLM request has a 1,024-completion-token cap including reasoning. There are no automatic retries. Calls may be billable or consume credits; effective monetary cost is not established by the existence of a deployment.

The batch reuses EXP-01's one-page DI invoice analysis and EXP-02's frozen source-only refinement prompt, schema, and grounding checks. The prompt/schema fingerprint is recorded. Ground Truth is read locally for input checks and scoring, but neither expected values nor test IDs or comparison outcomes enter the model request. The model receives only DI source text and the same generic extraction instructions. The original source files and workbook remain unchanged.

These are four files from an existing, already described fixture set, including a duplicate pair. They are not four independent or newly collected examples. The first exploratory invoice remains development data and is excluded from this batch. Conclusions must remain limited to the evaluated fixtures.

## Observation correctness versus workflow acceptance

All seven header fields remain in both baseline and refined comparisons. For the workbook's explicit missing-invoice-number marker, a missing extracted value is a correct absence observation; returning a fabricated number is incorrect. Correct absence does not satisfy a future required-field rule. Reports separate actual value matches from correct absence matches so the two are not conflated.

Missing refined values and raw/refined disagreements are flagged for review. Every case retains `review_required_pending_business_rules` as its workflow disposition, even if all observations match. Thresholds, required/optional fields, automatic supplier replacement, and final status rules have not been finalized. No invoice is automatically approved, paid, rejected, or posted.

T03/T04 are compared for equality of available refined header values; the report includes the number of compared fields. Matching available values are an observation only, not an implemented or validated duplicate key or duplicate-handling decision. T05 records DI's extracted line-item count against the fixture's two-position scenario; individual line-item values are not validated and the frozen LLM schema still contains header fields only.

## Authentication and run

Use the authenticated user terminal and private CLI configuration from EXP-01/02. The runner reads existing resource metadata, verifies DI kind/tier and model provisioning, and obtains existing keys only into memory, or uses explicitly configured environment keys. Entra authentication is attempted only when key authentication is unavailable. Tokens, keys, headers, resource URLs, and raw CLI errors are never printed or persisted in reports. No installs, resource creation, permission changes, or key rotations occur.

From the repository root, fill placeholders privately:

```powershell
python -B scripts/evaluate_invoice_batch.py --inventory '<private-inventory-json>' --input-dir '<synthetic-input-folder>' --ground-truth '<private-workbook-path>' --di-resource-name '<existing-resource>' --di-resource-group '<existing-group>' --approved-four-case-batch --synthetic-only
```

The CLI inventory format is the same as EXP-02. All four inputs are validated before service calls. Source bytes and workbook hashes are recorded privately. The workbook is checked again at completion for accidental changes.

## Persistent budget guard and failure behavior

The runner creates `private/exp03/budget/batch-started.private.json` exclusively after input, resource, and authentication checks. Each case/service also gets an exclusive attempt marker immediately before its request. The fixed allowlist is T02–T05 and services `di`/`llm`, enforcing at most eight attempts across invocations. EXP-02's consumed guard is untouched.

The first blocked case stops the batch; no subsequent cases or retries run automatically. DI polling is part of its single analysis operation, not another analysis submission. A failed/timed-out attempt remains consumed because service-side processing cannot be ruled out. After a batch has started, rerunning it is blocked before discovery. Do not delete guards or use a new directory to bypass them. Review saved evidence and explicitly agree any resume/new budget separately.

Input/discovery/authentication failures before creating the batch guard consume no analysis/inference attempts. Such preflight blockers can be corrected before running the batch again. No service request is made merely by running offline tests.

## Private evidence and interpretation

Each run writes `private/exp03/<run-id>/summary.private.json` and per-case directories containing DI response, the exact credential-free model request, completion, refined fields, comparison, usage when validated, elapsed time, and blocker details. If grounding fails, completion usage remains available in the saved completion body even when not copied into the case report. No original PDFs are copied into public tracking.

Summary status `completed` means all four cases reached evaluation, not that all fields matched or any workflow acceptance criterion was satisfied. Exit `0` means completed evaluation; exit `2` means blocked or invalid. Inspect field matches, correct absences, review reasons, duplicate observations, and item counts independently. No accuracy, latency, or cost generalization should be made from these few related fixtures.

Run offline tests with `python -B -m unittest discover -s tests -v`. Tests exercise expected absence, fabricated values, review flags, service/case guards, no-retry behavior, and provisional duplicate observations using invented fixtures.
