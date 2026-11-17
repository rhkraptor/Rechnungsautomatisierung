# Public project status

Report version: 0.3.0

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

The supplier name was present in a separate address-recipient field, while the primary supplier-name field selected a document heading. Raw extraction and expected values were preserved privately; no fallback was applied and the mismatch remains. The run took approximately 10.35 seconds including discovery, authentication, polling, and comparison; this is not an extraction-only latency benchmark. One invoice does not establish general accuracy. Entra-token extraction previously returned HTTP 401; its cause is unresolved.

Next priority: agree on supplier-name review/validation behavior and evaluate it separately from raw extraction, then extend testing to additional synthetic cases. Storage/mailbox integration has not started.

Publishing this report requires separate approval. It becomes retrievable through GitHub only after an approved commit and push; local preparation does not publish it. Future updates must cite only sanitized, shareable milestone evidence and must not include raw API output or private references.
