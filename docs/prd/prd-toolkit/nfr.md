<!-- Format: references/prd-format.md, "Requirement blocks". -->

# Non-functional requirements

### NFR-019 A test run leaves no cached uv environments behind
Status: approved
Flow: 1. the test session starts and points `UV_CACHE_DIR` at its test cache → 2. tests run uv
      scripts and git hooks, whose environments land in the test cache → 3. the session ends and
      deletes the test cache's `environments-v2` folder, keeping the downloaded packages
Acceptance (EARS):
- AC-019.1 While a pytest session over `prd-toolkit/tests/` runs, every uv command a test starts,
  a git hook's included, shall use the session's test cache: the folder that `PRD_TEST_UV_CACHE`
  names, or `prd-toolkit/.uv-test-cache/` when it is unset or empty.
- AC-019.2 When a pytest session over `prd-toolkit/tests/` ends, the harness shall delete the
  `environments-v2` folder of its test cache, keep the test cache's other folders, and leave the
  `environments-v2` folder of the uv cache it was started from with 0% more entries than it held
  when the session started.
Errors: -
Edge cases: a run split across pytest-xdist workers is one session: the environments are deleted
  once, when the whole run ends, never while a worker still runs; the test cache's downloaded
  packages stay, so only the first run in a worktree needs the network (T-019.2's inner session,
  which starts from an empty test cache, needs it on every run)
Tests: T-019.1 [integration], T-019.2 [integration]  (test-cases/nfr.yaml)
Traces: E-008; testing.md Harness, Clean state

## Observability

Not applicable: CLI scripts with no service; output goes to stdout and stderr, and there are no logs or metrics.
