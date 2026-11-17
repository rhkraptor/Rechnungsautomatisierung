# Experiment helpers

`extract_invoice.py` implements EXP-01 with the Python standard library and existing Azure CLI. See `docs/EXP-01.md`. It reads only an existing resource and submits a synthetic document for analysis. It does not create or reconfigure cloud resources. Authentication and detailed evidence remain private.

`refine_invoice.py` implements the single-attempt EXP-02 hosted comparison. It reuses saved source text, captures credentials only in memory, enforces the approved completion-token cap, and evaluates Ground Truth only after inference. Read `docs/EXP-02.md` before running it.

`evaluate_invoice_batch.py` evaluates four additional synthetic fixtures under a separate fixed budget. It keeps correct absence distinct from required-field acceptance and preserves provisional review dispositions. Read `docs/EXP-03.md`; never remove attempt guards to retry a started batch.
