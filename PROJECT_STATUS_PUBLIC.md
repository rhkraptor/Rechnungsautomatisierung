# Public project status

Report version: 0.6.0

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
| EXP-03 bounded batch runner | Implemented; live results pending | Four synthetic files; at most four DI analyses and four capped LLM requests, no retries; existing resources only |
| Combined offline suite | Passed | Twenty-nine tests; no hosted inference performed by tests |

The supplier name was present in a separate address-recipient field, while the primary supplier-name field selected a document heading. Raw extraction and expected values were preserved privately; no fallback was applied and the mismatch remains. The run took approximately 10.35 seconds including discovery, authentication, polling, and comparison; this is not an extraction-only latency benchmark. One invoice does not establish general accuracy. Entra-token extraction previously returned HTTP 401; its cause is unresolved.

The authorized single user-terminal inference completed with 564 prompt tokens and 280 completion tokens (844 total), within the 1,024-completion-token cap, with no automatic retries. End-to-end refinement run time was approximately 9.90 seconds, including discovery, authentication, inference, grounding and comparison; this excludes the earlier DI extraction. All seven returned fields passed local source-grounding checks and matched the unchanged workbook. The supplier-name mismatch was corrected in the separate refined result. No numerical model confidence was invented. The one-attempt authorization is consumed and the guard remains in place.

The request contained only saved DI source text and generic extraction instructions; Ground Truth was loaded separately for evaluation after inference. This invoice had already informed development, so 7/7 is an exploratory result, not independent validation or evidence of general accuracy. Inference worked using existing-resource key authentication; Entra-token access remains unresolved and effective monetary cost/credit coverage is not verified.

The additional four-file evaluation is authorized within its fixed budget. Missing-number absence is evaluated separately from field completeness; duplicate-content observations and a two-position item-count observation do not implement final workflow rules. The fixture set contains a duplicate pair and is not independent validation data. All cases remain subject to review while business rules are provisional. Agent execution stopped during preflight without consuming service attempts; authenticated user-terminal execution is pending. Thresholds remain undecided. Storage/mailbox integration has not started.

Publishing this report requires separate approval. It becomes retrievable through GitHub only after an approved commit and push; local preparation does not publish it. Future updates must cite only sanitized, shareable milestone evidence and must not include raw API output or private references.
