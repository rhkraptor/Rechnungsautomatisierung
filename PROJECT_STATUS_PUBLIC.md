# Public project status

Report version: 0.2.0

Updated: 2026-11-17

This report contains public milestones only. It does not reproduce internal assessments, discussions, identities, resource details, or evidence artifacts.

| Milestone | Status | Evidence scope |
|---|---|---|
| Minimal local repository layout | Prepared | Documentation and placeholder template exist locally |
| Private-by-default tracking policy | Prepared | Exact-path allowlist in `.gitignore`; publication guidance documented |
| Proposed architecture and five test scenarios | Documented | Public design descriptions only |
| EXP-01 reproducible runner | Implemented locally | Standard-library Python; read-only discovery, analysis, private evidence, seven-field comparison |
| Azure Document Intelligence extraction | Blocked in agent environment | Existing CLI profile inaccessible; private profile requires authentication; sign-in TCP connection denied; no extraction submitted |
| SharePoint integration | Not verified | No successful read/write run evidenced here |
| Outlook intake | Not verified | No successful trigger/attachment run evidenced here |
| Power Automate orchestration | Not verified | No successful connector or end-to-end run evidenced here |
| EXP-01 offline tests | Passed | Ten tests of comparison, workbook parsing, and mocked HTTP behavior; not live Azure evidence |

Next priority: authenticate in the private CLI configuration, run the synthetic single-invoice experiment from an authorized environment, and inspect private evidence. Storage/mailbox integration has not started.

Publishing this report requires separate approval. It becomes retrievable through GitHub only after an approved commit and push; local preparation does not publish it. Future updates must cite only sanitized, shareable milestone evidence and must not include raw API output or private references.
