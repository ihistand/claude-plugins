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
2. Update the marketplace (actor: agent) (env: production)
   Run: `claude plugin marketplace update ihistand`
   Check: `claude plugin marketplace list`
3. Update the plugin at each installed scope (actor: agent) (env: production)
   Run: `claude plugin update prd-toolkit@ihistand --scope user`
   Check: `claude plugin list`
4. Reload open sessions (actor: human) (env: production)
   Do: run /reload-plugins in each open Claude Code session
   Check: the session lists the new version

## Secrets

- None: a release uses the maintainer's own GitHub access; no secret is stored.
