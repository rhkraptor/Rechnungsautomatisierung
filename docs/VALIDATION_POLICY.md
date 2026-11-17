# Local validation and tester review - policy v0.1

## Current project decisions

All seven fields are mandatory: supplier, invoice number, invoice date, due date, net amount, VAT amount, and gross amount. Missing or invalid fields require review. A correctly extracted absence can match Ground Truth during an experiment while still failing this completeness policy.

When raw DI and source-grounded LLM values disagree, retain both and require tester review. The refined value is not automatically accepted merely because it matches a fixture or has a source quotation. Manual review is the current policy; fully automated handling is the long-term objective, requiring separately agreed acceptance rules and broader validation.

Matching supplier plus invoice number flags suspected duplicates for review. Never delete, reject, merge, or pay automatically. Duplicate keys normalize Unicode NFC and whitespace while preserving case and punctuation. They are heuristic signals, not proof of duplicate accounting transactions. Missing keys do not match other missing keys. Both/all records in a matching group are flagged.

These decisions define the project's current local policy, not university accounting requirements or independently confirmed team-wide consensus. Numeric confidence thresholds remain undecided. No LLM confidence is invented or substituted for DI confidence.

## Deterministic checks and limits

- All seven required values must be present with appropriate text/date/amount types.
- Dates must be valid ISO calendar dates; no payment/due-date chronology rule is inferred.
- Amounts must be finite decimals. Boolean, nonnumeric, NaN, and infinite amounts require review.
- Net plus VAT must equal gross using decimal arithmetic with no configured tolerance. This exact synthetic-POC check continues the experimental convention; real invoice rounding/credit-note rules remain outside the validated scope.
- Source grounding must have been independently verified by the caller; the replay helper rechecks saved quotations and normalized values against the saved source, and verifies the saved request matches the frozen source-only builder.
- DI/LLM disagreements are compared after Unicode/whitespace and decimal normalization. Numerical formatting alone does not create a disagreement.
- Duplicate matching is limited to the records supplied in a particular evaluation. No persistent invoice register or cross-system search is connected.

Results are `checks_passed` or `review_required`, with structured reason codes and `automatic_approval: false`. Passing local checks is not a payment decision, posting, human approval, or demonstrated production readiness. Every flagged record retains its evidence; a tester resolution is a separate action not implemented by this replay script.

The validator does not use Ground Truth, perform inference, read credentials, or call cloud services. The unchanged experimental match scores remain separate from these workflow-oriented checks. Individual invoice positions, currency-consistency policy, numeric confidence thresholds, payment status, and production duplicate semantics require further design or testing.

## Module contract

`src/invoice_validation.py` exposes `evaluate_records(records)`. Each record supplies a unique nonempty `record_id`, plain `raw` and `refined` field-value dictionaries, and `source_grounding_validated` set to true only after source checks. Unknown metadata is ignored. The function returns decisions in input order without modifying the records. Invalid record identity/container structure raises `ValueError`; invoice-content problems produce review reasons.

Use typed fields already normalized by the extraction/refinement adapters; raw OCR `content` is not a substitute for a missing typed value. The replay helper converts the saved DI/refined structures into this interface. Neither expected fixture values nor experiment pass/fail labels determine the decision.

## Offline replay

From the repository root, fill paths privately:

```powershell
python -B scripts/validate_saved_results.py --development-di-run '<private-di-run>' --development-refinement-run '<private-refinement-run>' --batch-run '<private-four-case-run>'
```

No cloud authentication or workbook is needed. Each run saves new private `records.private.json`, `report.private.json`, and `manual-review-queue.private.json` under `private/validation/<run-id>/`. Queue entries contain raw/refined values, decision reasons, and an empty tester-resolution field. Original experiment evidence and spent-call guards are untouched. Exit `0` means replay completed, not that invoices were approved; exit `2` indicates unavailable/invalid saved evidence.

The five-fixture replay produced five review-required records: all five have supplier-name disagreements, one is missing its mandatory invoice number, and two form a suspected-duplicate pair. No invoices were automatically approved. This demonstrates execution of the selected local policy on known fixtures, not an independent review outcome or production integration.

Run `python -B -m unittest discover -s tests -v` for offline checks, including all seven mandatory fields, disagreement review, invalid dates, invalid amounts, arithmetic errors, duplicate groups, and no automatic approvals.
