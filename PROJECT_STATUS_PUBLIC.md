# Public project status

Report version: 0.8.0

Updated: 2026-11-17

This report contains public milestones only. It does not reproduce internal assessments, discussions, identities, resource details, or evidence artifacts.

| Milestone | Status | Evidence scope |
|---|---|---|
| Minimal local repository layout | Prepared | Documentation and placeholder template exist locally |
| Private-by-default tracking policy | Prepared | Exact-path allowlist in `.gitignore`; publication guidance documented |
| Proposed architecture and five test scenarios | Documented | Public design descriptions only |
| EXP-01 reproducible runner | Implemented locally | Standard-library Python; read-only discovery, analysis, private evidence, seven-field comparison |
| Azure Document Intelligence extraction | Verified for one synthetic single-page invoice | User-terminal run with environment-supplied key completed analysis; agent authentication/network restrictions remain |
| EXP-01 Ground Truth comparison | 6 of 7 fields matched; overall mismatch | Supplier name was misclassified; invoice ID, both dates, subtotal, tax, and total matched |
| SharePoint integration | Not verified | No successful read/write run evidenced here |
| Outlook intake | Not verified | No successful trigger/attachment run evidenced here |
| Power Automate orchestration | Not verified | No successful connector or end-to-end run evidenced here |
| EXP-01 offline tests | Passed | Ten tests of comparison, workbook parsing, and mocked HTTP behavior; not live Azure evidence |
| EXP-02 hosted refinement | Verified on the same exploratory invoice | Existing GPT-5 mini deployment; baseline 6/7 fields matched, source-grounded refinement 7/7; original baseline preserved |
| EXP-03 bounded batch | Completed and locally replay-verified | Four DI analyses and four capped LLM requests; baseline 23/28 observations matched, refined 28/28; no automatic retries |
| Local validation policy v0.1 | Implemented and replayed | All seven fields mandatory; tester review for disagreements; supplier/invoice-number suspected-duplicate flags |
| Five-fixture policy replay | Completed locally | Five review-required records; missing mandatory number and duplicate pair also flagged; zero cloud calls or automatic approvals |
| Combined offline suite | Passed | Forty-two tests; no hosted inference performed by tests |

The supplier name was present in a separate address-recipient field, while the primary supplier-name field selected a document heading. Raw extraction and expected values were preserved privately; no fallback was applied and the mismatch remains. The run took approximately 10.35 seconds including discovery, authentication, polling, and comparison; this is not an extraction-only latency benchmark. One invoice does not establish general accuracy. Entra-token extraction previously returned HTTP 401; its cause is unresolved.

The authorized single user-terminal inference completed with 564 prompt tokens and 280 completion tokens (844 total), within the 1,024-completion-token cap, with no automatic retries. End-to-end refinement run time was approximately 9.90 seconds, including discovery, authentication, inference, grounding and comparison; this excludes the earlier DI extraction. All seven returned fields passed local source-grounding checks and matched the unchanged workbook. The supplier-name mismatch was corrected in the separate refined result. No numerical model confidence was invented. The one-attempt authorization is consumed and the guard remains in place.

The request contained only saved DI source text and generic extraction instructions; Ground Truth was loaded separately for evaluation after inference. This invoice had already informed development, so 7/7 is an exploratory result, not independent validation or evidence of general accuracy. Inference worked using existing-resource key authentication; Entra-token access remains unresolved and effective monetary cost/credit coverage is not verified.

The authenticated user-terminal batch completed. Per-case baseline scores were 5/7, 6/7, 6/7, and 6/7; refined scores were 7/7 each. The 28 refined matches comprise 27 populated values plus one correct absence. Four supplier-name assignments improved; a textual missing-number placeholder was normalized to null. Correct absence remains distinct from field completeness and does not approve the incomplete invoice. All request bodies were verified against the frozen source-only builder, and saved source hashes, grounding, scores, and attempt guards were checked locally without new service calls.

The duplicate pair matched on seven available refined header values, without an automatic duplicate decision. DI reported two items for the two-position fixture; individual item values remain unvalidated. All cases retain provisional review-required dispositions. The four files include a duplicate pair and share synthetic layout characteristics, so 28/28 is fixture-level observation agreement, not a general accuracy estimate.

Batch LLM usage was 2,269 prompt tokens and 1,090 completion tokens (3,359 total); every request stayed below its 1,024-completion-token cap. Effective monetary cost/credit coverage remains unverified. The four-plus-four attempt budget is consumed and guards remain in place.

The user selected all seven tested fields as mandatory, tester review of DI/LLM disagreements, and suspected-duplicate flags for matching supplier plus invoice number without deletion/rejection. These choices are implemented as local policy v0.1. Replay uses saved source evidence and extracted values, not Ground Truth, and produced five review-required records because all five have supplier-name disagreements; the missing-number fixture and both duplicate-group members have additional flags. Correct refined values remain preserved. Full automation is the long-term objective; no automatic approval or review resolution is implemented. Numerical confidence thresholds remain undecided. Storage/mailbox integration has not started. Next: tester resolution of the private queue and further acceptance-policy design before integration.

Publishing this report requires separate approval. It becomes retrievable through GitHub only after an approved commit and push; local preparation does not publish it. Future updates must cite only sanitized, shareable milestone evidence and must not include raw API output or private references.
