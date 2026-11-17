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

There is no runnable application or test command yet. No installer, provisioning script, dependency manager configuration, or deployment automation is included.

## Layout

| Path | Responsibility |
|---|---|
| `src/` | Future Python validation logic |
| `tests/` | Future offline validation tests and reviewed synthetic fixtures |
| `scripts/` | Future PowerShell configuration and test helpers |
| `powerautomate/` | Sanitized workflow documentation and future reviewed definitions |
| `config/` | Placeholder configuration template |
| `docs/` | Public architecture and publication policy |

Private context, course documents, original test artifacts, and detailed evidence are excluded. Public content must contain no credentials, personal information, private links, local absolute paths, or environment identifiers. Review each file and its staged diff before any separately approved commit; never stage the whole workspace.
