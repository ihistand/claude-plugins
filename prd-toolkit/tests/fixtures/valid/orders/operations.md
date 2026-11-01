# Operations

## Environments

| Environment | URL | Production |
|---|---|---|
| local | http://localhost:8080 | no |
| ci | none; runs inside the pipeline | no |
| staging | https://orders-staging.example.com | no |
| production | https://orders.example.com | yes |

## Runbook

1. Deploy to staging (actor: agent) (env: staging)
   Run: `./deploy.sh staging`
   Check: `curl -fsS https://orders-staging.example.com/health` prints `ok`
   Rollback: `./deploy.sh staging --previous`
2. System tests on staging (actor: agent) (env: staging)
   Run: tests system, e2e
3. Approve production (actor: human) (env: production)
   Do: read the staging results and reply "deploy production"
   Check: the reply says "deploy production"
4. Deploy to production (actor: agent) (env: production)
   Run: `./deploy.sh production`
   Check: `curl -fsS https://orders.example.com/health` prints `ok`
   Rollback: `./deploy.sh production --previous`
5. Smoke on production (actor: agent) (env: production)
   Run: tests smoke

## Secrets

- GEOCODER_API_KEY: Secret Manager, mounted as an environment variable by `deploy.sh`.
- ORDERS_TEST_ADMIN_TOKEN, ORDERS_TEST_REP_TOKEN: Secret Manager, staging only; the bearer tokens
  of the test-admin and test-rep identities.
