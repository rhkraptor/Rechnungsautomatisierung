# Python validation

`invoice_validation.py` implements policy v0.1 as pure standard-library logic, separate from service access. All seven fields are mandatory; disagreements and suspected duplicates require tester review. No cloud calls, credential handling, Ground Truth lookup, or automatic approvals occur here. See `docs/VALIDATION_POLICY.md` for the contract and scope.
