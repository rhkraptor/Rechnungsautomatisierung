# Validation tests

Run `python -B -m unittest discover -s tests -v` for offline comparison, workbook parsing, and mocked HTTP tests. Fixtures are invented and contain no original invoice artifacts. Tests never call Azure. Temporary workbook fixtures stay under ignored `private/test-temp/`.

Duplicate and line-item validation remain future work. Live extraction is a separate, explicitly invoked experiment; an offline pass is not evidence of Azure access.

EXP-02 checks cover the capped source-only request, endpoint restrictions, inventory compatibility, source grounding, unsupported values, date/amount normalization, missing fields, and the persistent single-attempt guard. They never invoke a hosted model.

EXP-03 adds absence semantics, fabricated-number rejection, disagreement review, per-case/service guards, failure without retries, started-batch protection, and header-equality observations without automatic duplicate decisions.

Local policy checks cover all seven mandatory fields, tester review of grounded corrections, invalid dates and nonfinite amounts, arithmetic, exact-key suspected duplicates, and separation from fixture Ground Truth and automatic approval.
