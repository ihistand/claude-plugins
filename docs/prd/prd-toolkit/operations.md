<!-- Format: references/prd-format.md, "operations.md". -->

# Operations

## Environments

| Environment | URL | Production |
|---|---|---|
| local | none | no |
| production | https://github.com/ihistand/claude-plugins | yes |

## Runbook

1. Approve the release (actor: human) (env: production)
   Do: review the release pull request on GitHub and merge it into `main`
   Check: the pull request shows as merged
2. Update the installed plugin (actor: agent) (env: production)
   Run: `claude plugin update prd-toolkit@ihistand`
   Check: `claude plugin list`

## Secrets

- None: a release uses the maintainer's own GitHub access; no secret is stored.
