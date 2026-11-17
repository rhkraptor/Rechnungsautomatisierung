# Public repository boundary

The working directory is private by default. `.gitignore` allows only exact reviewed paths; an allowlisted path is a candidate, not publication approval. Changes to existing public files require renewed review.

## Before any approved commit

1. Inspect every intended file in full, including hidden metadata and generated content. Check secrets, passwords, tokens, authentication files, subscription and tenant identifiers, personal email addresses, internal links, private collaboration links, names identifying contributors, absolute local paths, and private discussions.
2. Keep private context, internal status, transcripts, course materials, original invoice artifacts, raw API responses, workflow exports, screenshots, logs, and local configuration excluded. Sanitize any deliberately selected public derivative separately.
3. Inspect `git status --short --untracked-files=all` and explicitly name each file to stage. Never use bulk staging. Review `git diff --cached` and the full staged file list before committing.
4. Verify repository-local Git author name and privacy-preserving email against the authenticated owner's identity. Do not use invented identities or automatic AI co-author trailers. Scientific AI disclosure is maintained separately.
5. Run an available secret scanner when present, plus manual review. A clean scan does not prove that content is public-safe. Do not install tools without approval.
6. Commit and push only after explicit approval for publication. Re-review staged content if anything changes after approval.

## Limits

Ignore rules do not remove already tracked files and can be overridden by force-adding. Never force-add private files. Git author and committer metadata are public after publication; keep both privacy-preserving. If private data enters a commit, stop publication and assess removal; if a credential is exposed, revoke/rotate it.

Credentials must come from environment variables or an approved secret store. Never print them in commands, responses, logs, or errors. Sanitized examples must use placeholders only. Exported Power Automate definitions may contain connection references, addresses, resource identifiers, and URLs and require full review.
