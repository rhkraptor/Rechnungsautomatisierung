# Invoice automation

A university Digital Factory project exploring AI-assisted invoice processing with Power Automate. The goal is to extract structured invoice data, validate it, handle exceptions, and measure processing quality and effort using synthetic data only.

## Proposed architecture

```text
Outlook attachments -> Power Automate -> SharePoint source storage
                                      -> Azure Document Intelligence
                                      -> Validation and review
                                      -> SharePoint invoice register
```

Power Automate is the primary workflow environment. Python will support automated validation and tests; PowerShell and Azure CLI will support reproducible configuration and diagnostics where practical. These integrations are planned and have not been demonstrated by this repository.

## Status

Repository preparation and public documentation are available. No extraction API, connector integration, or end-to-end workflow is verified here. See [PROJECT_STATUS_PUBLIC.md](PROJECT_STATUS_PUBLIC.md) for the versioned public milestone report and [architecture](docs/ARCHITECTURE.md) for scope and test descriptions.

## Development setup

1. Use an existing Git installation and an editor such as VS Code. PowerShell and Python 3 are the intended local tools; Azure CLI is needed only for later authorized cloud work. No runtime dependencies are defined yet.
2. Read [publication rules](docs/PUBLICATION.md). All new paths are ignored until individually reviewed and explicitly allowlisted.
3. For future local configuration, copy `config/.env.example` to a private `.env` file. Supply settings locally through environment variables or an approved secret store. The template is documentation only; no dotenv loader is included.
4. Use synthetic inputs only. Keep raw responses, authentication data, resource identifiers, and detailed evidence outside public tracking.
5. Verify permissions and licensing before testing services. Use an existing authorized SharePoint site and mailbox. Explain intended cloud changes before executing them.

EXP-01 now provides a standard-library Python extraction runner and offline tests. See [the experiment guide](docs/EXP-01.md). Run `python -B -m unittest discover -s tests -v` for offline tests; these do not call Azure. No packages need to be installed. Cloud extraction has not yet succeeded in the agent environment.

[EXP-02](docs/EXP-02.md) adds a single-attempt hosted refinement runner using saved DI text, strict structured output, source grounding checks, and separate Ground Truth evaluation. On the initial exploratory invoice, the DI baseline matched 6/7 fields and refinement matched 7/7. This does not establish general accuracy. Original extraction evidence remains unchanged, and refinement requires no additional DI call.

[EXP-03](docs/EXP-03.md) prepares a bounded four-file evaluation with separate observation scores and provisional review dispositions. It includes missing-value semantics, header-equality observations, and line-item count reporting. Live batch results are not yet verified.

## Layout

| Path | Responsibility |
|---|---|
| `src/` | Reserved for future shared validation logic |
| `tests/` | Offline extraction/comparison tests using invented fixtures |
| `scripts/` | EXP-01 extraction runner; no provisioning commands |
| `powerautomate/` | Sanitized workflow documentation and future reviewed definitions |
| `config/` | Placeholder configuration template |
| `docs/` | Public architecture and publication policy |

Private context, course documents, original test artifacts, and detailed evidence are excluded. Public content must contain no credentials, personal information, private links, local absolute paths, or environment identifiers. Review each file and its staged diff before any separately approved commit; never stage the whole workspace.
