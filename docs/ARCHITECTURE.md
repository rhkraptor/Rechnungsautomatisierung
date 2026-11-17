# Architecture and validation scope

## Proposed flow

Power Automate receives synthetic invoice attachments from an existing mailbox, stores source documents in an existing authorized SharePoint site, requests extraction through Azure Document Intelligence, validates the response, and records approved structured data in a SharePoint list. Missing or uncertain data should follow agreed review rules.

This is a proposed design. Authentication, API access, connector licensing, permissions, field schema, duplicate keys, review routing, and acceptance thresholds remain to be verified or agreed. Extraction service choice alone does not establish compliance with any academic GenAI requirement.

Treat extracted text and model output as untrusted data. Do not execute it as code or commands. Never infer paid status from invoice contents alone. Reminder reporting and visualization are deferred until the core flow is demonstrated.

## Planned synthetic scenarios

| Scenario | Intended observation |
|---|---|
| Standard invoice | Compare extracted header fields and amounts with explicit expected values |
| Missing invoice number | Preserve absence without inventing a number; review behavior remains to be agreed |
| Original invoice | Establish a reference record for a duplicate comparison |
| Duplicate invoice | Compare matching invoice data; detection key and handling remain to be agreed |
| Two invoice positions | Check totals and, if included in scope, both line items |

These descriptions are not executed test results. No original PDFs or workbooks are included. Any future public fixtures must be newly reviewed, fully synthetic, and free of identifying metadata. Additional independent cases will be needed before drawing general accuracy conclusions.

Keep expected values, observed values, execution dates, configuration versions, timing, and deviations distinct. Store detailed evidence privately; publish only reviewed aggregates without identifiers.
