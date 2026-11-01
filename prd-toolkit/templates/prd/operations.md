<!-- Format: references/prd-format.md, "operations.md". -->

# Operations

## Environments

| Environment | URL | Production |
|---|---|---|
| [NEEDS CLARIFICATION: first environment] | [NEEDS CLARIFICATION: URL] | no |
| production | [NEEDS CLARIFICATION: production URL] | yes |

## Runbook

1. [NEEDS CLARIFICATION: deploy step title] (actor: agent) (env: [NEEDS CLARIFICATION: first environment])
   Run: [NEEDS CLARIFICATION: the deploy command, one backticked command]
   Check: [NEEDS CLARIFICATION: a backticked health command, then prints `<text>`]
   Rollback: [NEEDS CLARIFICATION: the previous-version command, one backticked command]
2. [NEEDS CLARIFICATION: system tests step title] (actor: agent) (env: [NEEDS CLARIFICATION: first environment])
   Run: tests system
3. [NEEDS CLARIFICATION: approval step title] (actor: human) (env: production)
   Do: [NEEDS CLARIFICATION: what the owner reads and replies]
   Check: [NEEDS CLARIFICATION: what the reply must say]

## Secrets

- [NEEDS CLARIFICATION: secret names and where each is stored; never the values]
