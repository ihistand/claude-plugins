# Operations

## Environments

| Environment | URL |
|---|---|
| local | http://localhost:8080 |
| ci | none; runs inside the pipeline |
| staging | https://orders-staging.example.com |
| production | https://orders.example.com |

## Runbook

1. Deploy the build with `./deploy.sh staging`, then run the system tests. (actor: agent)
2. Deploy to production with `./deploy.sh production` after the owner approves. (actor: human)

## Secrets

- GEOCODER_API_KEY: Secret Manager, mounted as an environment variable by `deploy.sh`.
- ORDERS_TEST_ADMIN_TOKEN, ORDERS_TEST_REP_TOKEN: Secret Manager, staging only; the bearer tokens
  of the test-admin and test-rep identities.
