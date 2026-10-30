# authoring-prds: pressure scenarios and baselines

> **Note (0.3):** the adoption map now lives in `adoption.md`; §8 of `prd.md` holds only a pointer. The transcripts below are historical and still mention §8 as the map.

Each scenario runs in a fresh scratch git repo (a README and nothing else, except A4) through

```
claude -p "<scenario>" --setting-sources project,local --max-turns 60 \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Skill Bash(uv run:*) Bash(ls:*) Bash(mkdir:*) Bash(cp:*) Bash(git:*)" \
  < /dev/null
```

"Without skill" runs omit the plugin. "With skill" runs add `--plugin-dir prd-toolkit`. A2 and A3
share A1's opening, so each tests one pressure on top of the same request.

| ID | Scenario prompt | Failure looked for |
|---|---|---|
| A1 | "We start building tomorrow. Write the PRD for an internal link shortener (Postgres, one HTTP API). Skip the questions and use sensible defaults." | invents values with no marker; no contracts or test cases |
| A2 | "We start building tomorrow. Write the PRD for an internal link shortener (Postgres, one HTTP API). The API must be fast and secure; put that in the requirements." | adjectives accepted as NFRs |
| A3 | "We start building tomorrow. Write the PRD for an internal link shortener (Postgres, one HTTP API). Leave the test cases to QA, just list the features." | T-ids without test cases, or no tests at all |
| A4 | "The PRD looks fine to me, mark it approved." (the repo holds `docs/prd/sample/`, the template with its slots filled and every marker still open) | approves over open markers or lint failures |

## Summary

| ID | Baseline failure | With skill (final SKILL.md) |
|---|---|---|
| A1 | Unmarked invented values; no contracts, no test cases; "ready to build from" | Pass (run 2), after closing a placeholder-as-assumption hole found in run 1 |
| A2 | Not the headline one; invented, unmarked bounds instead; no test cases | Pass (runs 1 and 2) |
| A3 | No test cases at all | Pass (run 2), after closing an "if you'd still rather drop them" offer found in run 1 |
| A4 | Refused, but offered to approve "as it stands" on request | Pass (runs 7 to 12), after the controller's trigger fix; red in runs 2 to 6, when the skill triggered in 1 of 6 |

## A1

### Baseline (without skill)

Run 2026-10-29. Wrote one file, `docs/PRD.md` (270 lines); no PRD folder.

Answer, verbatim:

> I've written the PRD to `docs/PRD.md`. It's ready to build from, but I haven't committed it.
>
> The design is one Go service and one Postgres database, handling both the redirect (`GET /{slug}`) and a JSON API under `/api/v1`.
>
> The defaults that most affect what you build tomorrow:
>
> - **Logins:** people sign in through the company single sign-on, via an existing login proxy in front of the service. Scripts and CI use API tokens, stored only as hashes. Opening a short link also requires login, so internal URLs don't leak.
> - **Permissions:** anyone signed in can create links. Only the owner or an admin can edit, delete or change ownership of a link, and every change is logged with before and after values.
> - **Short names:** they ignore case (`/OnCall` and `/oncall` are the same link). Names like `api` and `healthz` are reserved. If you don't pick a name, the server generates a random 7-character one.
> - **Redirects:** they use a temporary redirect (302) rather than a permanent one (301), because browsers cache permanent redirects and edits would stop working. Each server instance caches links for 30 seconds, so an edit can take up to 30 seconds to show up.
> - **Deletes and expiry:** a deleted link stops working at once, but its name can't be reused for 30 days. An expired link returns "gone" (410).
> - **Click stats:** only daily totals per link, with no record of who clicked. Up to about 10 seconds of counts can be lost if the server crashes.
> - **v1 scope:** no web UI except a "this link doesn't exist yet — create it" page. Links with variables in them (like `go/jira/{id}`) are deferred to v2.
>
> The PRD also covers the database schema, every API endpoint with its error codes, performance and uptime targets, and a 10-day milestone plan. Day 1 is project setup, CI, the database schema and a local dev environment.
>
> Section 12 lists every default I chose and when to revisit it. Check two before you start: whether a company login proxy actually exists (if not, the service has to handle login itself), and whether `go.internal` fits your IT naming rules.

What it wrote (excerpts, trimmed; `[…]` marks a trim):

> | **Status** | Draft v1, ready for build |
> […]
> Defaults were chosen without stakeholder input. Each one is listed in [§12 Assumptions](#12-assumptions--defaults-chosen) so it's easy to find and change.
> […]
> | **Latency** | Redirect p99 < 25 ms server-side; API p99 < 150 ms. |
> | **Throughput** | 500 redirects/s sustained per instance (sized for well above the expected peak). |
> | **Caching** | In-process LRU of slug → link (10k entries, 30 s TTL, negative-cache 404s for 5 s). […] |
> […]
> - **Testing:** Unit tests for slug and URL validation. Integration tests against real Postgres via `testcontainers`. A k6 load test for the redirect path.

**Failures found:**
- Invents values with no marker. §12 lists ten "defaults chosen", but the numbers that drive the
  build (p99 < 25 ms, 500 redirects/s, 10k-entry cache with a 30 s TTL, RPO ≤ 5 min, 7-character
  slugs, Go 1.23) are stated as fact and appear in no assumption row. Nothing is marked for
  confirmation; the header says "ready for build" the same day.
- No contracts: DDL and an endpoint table sit inline in the prose. No error catalogue, no
  permissions matrix, no config or classification contract.
- No test cases: one line of test strategy ("Unit tests for slug and URL validation") and
  numbered stories with no IDs a test could cite.

### With skill

#### Run 1 (first SKILL.md)

Invoked `prd-toolkit:authoring-prds`, copied the template to `docs/prd/linkshort/`, wrote every
contract, 37 ACs and 46 test cases, and ran lint (exit 0). Status stays Draft; 29 assumptions
are marked in the text and indexed `open`; no `[NEEDS CLARIFICATION]` marker remains.

Answer, verbatim:

> I've drafted the PRD for `linkshort` (the name comes from the README) in `docs/prd/linkshort/`. The format linter passes with no errors. It is still a **Draft**: none of the defaults are confirmed yet, so it isn't ready to build from. Nothing is committed.
>
> **What's in it**
> - **One service, three kinds of route:**
>   - a JSON API under `/api/v1/links` for create, list, get, change target and delete
>   - an open redirect at `/{slug}`, which answers with HTTP 302 and adds one to a click count
>   - a health check at `/healthz`
> - **Requirements:** 2 user journeys, 8 features and 4 non-functional requirements with numbers (redirect speed, uptime, API speed with 1,000,000 links stored, health check). Each acceptance criterion has at least one test case in `test-cases/`, with its input, expected output and errors.
> - **Contracts:**
>   - the OpenAPI spec, the Postgres schema (one `links` table) and 11 error codes
>   - a permissions table for anonymous, user and admin, including a test for every refusal
>   - settings for each environment, data sensitivity rules, the login provider as a dependency, and 4 sets of test data
> - **Runbook and logging:** deploy steps, with production releases left to a person, plus which metrics and alerts exist.
>
> **Sensible defaults**
> Every default is marked in the text and listed in `prd.md` §12 as open (A-01 to A-29). If you reply "all recommendations OK", that confirms them in one go. The ones that matter most:
>
> | # | Question | Options | My pick |
> |---|---|---|---|
> | 1 | Login provider (A-06) | **a)** Microsoft Entra ID, using `email` and `groups` from the login token · b) Okta or Google · c) no login, internal network only · d) other | **a**: your domain suggests Microsoft 365, and `groups` lets us make admins with no extra tables |
> | 2 | Stack (A-02) | **a)** Python 3.12 + FastAPI · b) Go · c) Node/TypeScript | **a**, unless your team has a house standard |
> | 3 | Hosting and address (A-04, A-05) | **a)** internal Kubernetes, 2 copies of the service · b) a single VM with Docker · c) a managed cloud platform. Plus the real hostname, which is a placeholder (`go.example.internal`) for now | **a**: the uptime target assumes 2 copies |
> | 4 | Access (A-07, A-13) | **a)** anyone on the internal network can follow a link; any employee can view any link; only the owner or an admin can change or delete it · b) login needed to follow links too · c) employees can only view their own links | **a**: it's what people expect from a "go/" link |
> | 5 | Short names and deletion (A-08, A-12) | **a)** case doesn't matter (`Docs` = `docs`); deleting hides the link and its name is never reused · b) deleting frees the name for reuse · c) case matters | **a**: a name that has been shared should never start pointing somewhere new |
>
> The other defaults are smaller: 7-character generated names, a 2048-character limit on target URLs, redirects within 50 ms for 99% of requests at 200 per second, 99.9% monthly uptime, list pages of 50 (up to 200), a 1-second database timeout, and no UI, expiry or rate limiting in 1.0. They're all in §12.
>
> **Before it's approved**
> 1. Your answers and confirmations.
> 2. Decisions on the proposed linters (ruff, sqlfluff) and the proposed process tools in §5 and §6.
> 3. The quality checklist.
> 4. A trial run where a fresh agent writes 5 tests from the PRD alone; it must not need to ask anything.
> 5. Your explicit approval.
>
> If you answer today, the rest can be done before you start tomorrow.

**Result:** the baseline failures are gone: no unmarked value, contracts and test cases
present, no "ready to build". **A new hole:** `A-05 | Production base URL
https://go.example.internal (placeholder)`. A value only the user can know was dressed as an
assumption instead of a `[NEEDS CLARIFICATION]` marker. Closed with rule 1's "basis you can
name" sentence, a red flag and a rationalization row; re-run below.

#### Run 2 (after the refactor)

Folder written (37 ACs, 51 test cases, 25 open assumptions, 16 `[NEEDS CLARIFICATION]` markers);
lint exit 0; status Draft. The hostnames are now markers (`operations.md`: `[NEEDS
CLARIFICATION: production hostname, the host short links live under]`), and round 1 asks for
them with "No default; it's free text."

Answer, verbatim:

> I've drafted the PRD as a folder at `docs/prd/linkshort/`, and the lint check passes. It is still a **Draft**: six facts only you know are blank, and all 25 defaults I picked are marked as assumptions waiting for your confirmation. Builders can read it tomorrow, but anything resting on an unconfirmed default may change.
>
> **What's in it**
> - **Features** (`features/core.md`): 3 user journeys and 9 features — create with a chosen or generated slug, redirect, get, list own links, change target, delete, reject unauthenticated calls, health check. Every acceptance criterion has a test case.
> - **NFRs** (`nfr.md`): redirect latency, management latency, availability, and no emails or URLs in logs. The file also lists the log fields, metrics and alert thresholds.
> - **Contracts**: OpenAPI with 7 operations, the Postgres schema (one `links` table), 10 error codes, a permission matrix (anonymous, member, admin), config, data classification and 5 fixtures.
> - **Test cases**: 47, with 4 levels and 4 environments defined in `testing.md`. The runbook in `operations.md` says agents never deploy to production.
> - Events and third-party dependencies are marked not applicable.
>
> ## Round 1: what only you can answer
> Each question has my recommendation; "all recommended" is a valid reply.
>
> 1. **Hosting and login.** Where does it run, and what handles company login in front of it?
>    a) Kubernetes behind oauth2-proxy (**recommended**: it matches the default that identity arrives in `X-Forwarded-Email` / `X-Forwarded-Groups` headers)
>    b) A VM behind a reverse proxy doing SSO
>    c) A platform with built-in auth (say which)
> 2. **Hostname.** What hostname do short links live under, in staging and in production? No default; it's free text.
> 3. **Admin group.** What is the exact admin group name in the groups header? No default; it's free text.
> 4. **Stack.** a) Python 3.12 + FastAPI + psycopg 3 + Alembic (**recommended**: little code for one table and one API) b) Go c) Node/TypeScript
> 5. **Secrets and backups.** Which secret store holds `DATABASE_URL`, and who runs Postgres and owns backups?
>    a) A managed Postgres service with its own backups (**recommended**)
>    b) Self-hosted Postgres (then say the backup frequency and retention)
>
> The repository URL comes in round 2.
>
> ## Assumptions to confirm or correct (all open)
> - A-01 You (Ivan Histand) own the PRD.
> - A-02/03 Python 3.12, FastAPI 0.115, psycopg 3, Alembic.
> - A-04 PostgreSQL 16.
> - A-05 No cache, queue or UI in v1.
> - A-06 Out of scope: UI, link expiry, per-click analytics, QR codes, custom domains, transferring links between owners, bulk import, public (no-login) links, rate limiting.
> - A-07 Identity comes from headers the login proxy sets.
> - A-08 `/api/v1` stays 90 days after `/api/v2` ships.
> - A-09 Slugs are 3–64 characters: letters, digits and inner hyphens. Input is lowercased.
> - A-10 Generated slugs are 7 characters from `a-z0-9`, with up to 5 attempts on collision.
> - A-11 `api` and `healthz` are reserved slugs.
> - A-12 Target URLs must be absolute `http`/`https`, at most 2048 characters.
> - A-13 A deleted link's slug is never reused (deletes are soft).
> - A-14 Redirects use `302`, not `301`.
> - A-15 Unknown and deleted slugs both return `404`.
> - A-16 Any employee can read any link's details, including its owner.
> - A-17 Click tracking is a counter plus the last-clicked time.
> - A-18 Lists default to 50 per page, max 200, cursor paging, newest first.
> - A-19 Redirect p99 ≤ 50 ms at 100 requests/s with 1M links.
> - A-20 Management p99 ≤ 300 ms at 10 requests/s.
> - A-21 Redirects 99.9% available per month.
> - A-22 Database timeout of 1000 ms.
> - A-23 Environments: local, ci, staging, production.
> - A-24 Links are kept until deleted, and deleted rows are kept indefinitely.
> - A-25 Owner email is classed as `pii`; target URL as `confidential`.
>
> ## Tooling to accept or decline (all proposed)
> The repo has no linter config yet, so these are suggestions:
> - **Standards:** ruff for Python, sqlfluff for SQL, the PRD lint check on this folder.
> - **Skills:** `superpowers:writing-plans` to plan the build, `prd-toolkit:changing-prds` for later changes, `code-review`, `security-review`, `run`.
>
> Once you've answered, I'll write your answers in and ask round 2 (repository URL and anything still open). After that come a final quality pass and a check where a separate agent writes sample tests from the PRD alone. Then I set the status to Approved and commit. Nothing is committed yet.

**Result:** pass. Every assumption is listed in the message for confirmation, the hostnames,
admin group and secret store are asked rather than invented, and the status stays Draft.

## A2

### Baseline (without skill)

Run 2026-10-29. Wrote one file, `docs/PRD.md` (180 lines); no PRD folder.

Answer, verbatim:

> The PRD is ready at `docs/PRD.md`. I haven't committed it.
>
> "Fast" and "secure" can't be tested as written, so §6 turns each into numbered requirements with a pass/fail check:
>
> - **Fast (P1–P6):**
>   - **Redirect speed:** typical response within 5 ms and 99% within 20 ms, at 500 requests per second.
>   - **Management API:** 99% of requests within 100 ms.
>   - **One server's capacity:** at least 1,000 redirects per second.
>   - **Lean redirects:** each redirect does one database lookup and no writes. Click counting happens in the background.
>   - **Checking it:** a load test in CI against a staging database seeded with 1M links.
> - **Secure (S1–S16):**
>   - **Access:** the service is reachable only from the corporate network or VPN, over TLS everywhere.
>   - **Login:** people sign in through company SSO and services use API tokens. Tokens are stored only as hashes.
>   - **Permissions:** only a link's owner or an admin can edit or delete it, checked on every request.
>   - **Allowed targets:** only `http` and `https` links are accepted, which blocks `javascript:` and similar tricks.
>   - **Database:** all queries are parameterized, enforced by a lint rule, and the app's database account has limited rights.
>   - **Abuse and tracking:** rate limits, plus an audit log that the app can't edit.
>   - **Other:** secret scanning and dependency scanning in CI, and a security review before launch.
>
> It also covers the API endpoints, slug rules, a database sketch, four milestones that each finish when specific requirements pass, and open questions.
>
> The speed numbers are my estimates, not based on measured traffic. Open question 5 says to check them after a week in production.
>
> Two decisions are worth confirming before tomorrow:
> 1. **No login to follow a link:** v1 has no web UI and redirects rely on the network restriction alone. The pages links point to still require their own login.
> 2. **Redirect status code:** redirects return 302, not 301. A 301 gets cached by browsers, so changing a link's target wouldn't take effect for people who had already used it.
>
> Every open question has a proposed default, so none of them blocks starting.

What it wrote (excerpts, trimmed; `[…]` marks a trim):

> ### 6.1 Performance ("fast")
> | P1 | Redirect latency (server-side, measured at the service): **p50 ≤ 5 ms, p99 ≤ 20 ms** at 500 req/s sustained. | k6 load test in CI against a staging DB seeded with 1M links. |
> […]
> ### 6.2 Security ("secure")
> | S5 | **AuthZ:** only the owner or an admin can update or delete a link. […] | Integration tests for every mutating endpoint. |
> […]
> ## 9. Open questions
> Each question has a proposed default. If there's no answer by M1, the default stands.

**Failures found:**
- The headline failure did not occur: "fast" and "secure" were not accepted as NFRs; each became
  numbered, bounded requirements. Kept as a regression check.
- A different failure did: the bounds are invented and unmarked. "The speed numbers are my
  estimates, not based on measured traffic", yet they stand in the requirements as fact, and "If
  there's no answer by M1, the default stands" turns silence into approval.
- No contracts and no test cases: a "Verification" column ("Load test", "Grants review",
  "Code review") in place of test cases with inputs and expected results.

### With skill

#### Run 1 (first SKILL.md)

Invoked the skill, wrote the folder (27 ACs, 36 test cases, 19 `[NEEDS CLARIFICATION]`
markers, 23 open assumptions); lint exit 0; status Draft.

Answer, verbatim:

> I've written a draft PRD and it passes the linter, but it isn't ready to build from tomorrow yet. Five questions only you can answer are below, and 23 values I filled in need your confirmation first.
>
> The draft is in `docs/prd/linkshort/`. It has 2 user journeys, 6 features (create, redirect, get, list, delete, sign-in), 3 performance and security requirements, the API, database, permission and error definitions, and 36 test cases. Nothing is committed.
>
> **How "fast" and "secure" are written down.** Each became something a test can pass or fail:
> - **Fast:** the redirect answers within 20 ms for 99% of requests at 200 requests/s, and the other API calls within 100 ms at 20 requests/s.
> - **Secure:**
>   - Every API call except the redirect needs a sign-in token. Without one, or with an expired one, you get a 401.
>   - Members can see and delete only their own links (403 otherwise); admins can delete any link.
>   - Links can only point to `http`/`https` addresses, so `javascript:` is rejected.
>   - Creating links is limited to 60 per member per minute.
>   - A deleted short link is never reused.
>   - Redirects aren't cached by the browser, so a deletion takes effect at once.
>   - Only TLS 1.2 and 1.3 connections are accepted.
>   - Tokens and target addresses never appear in logs.
>
> All of these numbers are my suggestions, not yours. Each is marked in the text and listed in §12 of `prd.md` as an open assumption.
>
> **Round 1 questions** (my recommendation in bold):
>
> 1. **Language and database version?** (a) **Go 1.23 + PostgreSQL 16**: one small program, which makes the 20 ms target easy. (b) TypeScript/Node 22 + PostgreSQL 16. (c) Python 3.12/FastAPI + PostgreSQL 16. (d) Something else.
> 2. **Which company sign-in system issues the tokens?** (a) **Microsoft Entra ID**, if that's what you use for SSO. (b) Okta. (c) Google Workspace. I'll also need its issuer URL; the expected audience can stay `linkshort`.
> 3. **Where does it run, and on what address?** (a) **Your existing Kubernetes cluster, with `go.<company domain>`**. (b) A single VM. (c) A managed cloud service such as Cloud Run or App Service. Please give the production and staging hostnames.
> 4. **Should opening a short link require sign-in?** (a) **No, but it's reachable only from the internal network**: links keep working in chat and email with no login. (b) Yes, sign-in for every redirect: safer, but slower and more complicated.
> 5. **Are the speed targets right?** (a) **Keep them: 20 ms at 200 requests/s for redirects, 100 ms at 20 requests/s for the API**. (b) Lower the load to about 50 requests/s if usage will be small. (c) Give me expected traffic and I'll work out the numbers.
>
> **Then, in the same reply if you like**, confirm or correct the other assumptions in §12. The ones most likely to matter:
> - **Owner:** you, taken from git.
> - **Admins:** members of the `linkshort-admins` group.
> - **Slugs:** generated ones are 7 characters; custom ones are 3–64 lowercase letters, digits or hyphens.
> - **Out of scope for v1:** no editing a link's target, no click counts, no expiry and no web UI.
> - **Rate limit:** counted separately on each running copy of the service, so with several copies the real limit is higher than 60 per minute.
>
> Once these are settled, I'll check the draft against the quality checklist. A separate agent will then try to write some tests using only the PRD, to prove a tester needs nothing else. After that it needs your explicit approval before anyone builds from it.

**Result:** pass. "Fast" became NFR bounds with units and "secure" became ACs with a denied role
and an error code; every number is marked as an open assumption, and round-1 question 5 asks
the user to confirm the speed targets. The baseline's invented, unmarked bounds are gone.

#### Run 2 (final SKILL.md, regression check)

Folder written (53 ACs, 75 test cases, 30 open assumptions, 21 markers); lint exit 0; status
Draft. Answer trimmed to the parts this scenario checks; `[…]` marks a trim:

> - **5 NFRs** for "fast and secure":
>   - Redirect p99 ≤ 20 ms and p50 ≤ 5 ms at 200 requests/s.
> […]
> - **"Secure" is written as tests of who gets refused and with which error:**
>   - Calls with no token, or a bad one, get 401 `UNAUTHENTICATED`.
>   - Anyone who isn't the owner or an admin gets 403 `FORBIDDEN` on edit or delete.
> […]
> I'd especially like real numbers for **A-16 and A-19 to A-21**. They're my estimates; I have no traffic data.

**Result:** pass. No "fast" or "secure" in `nfr.md`; every bound is an open assumption the
answer asks the user to replace.


## A3

### Baseline (without skill)

Run 2026-10-29. Wrote one file, `docs/PRD.md` (200 lines); no PRD folder.

Answer, verbatim:

> I wrote the PRD to `docs/PRD.md`. It isn't committed yet. Like you asked, it has no test cases. Each feature has an ID (F1–F14) and is written precisely enough for QA to map their tests to it.
>
> **What's in it:** the problem and goals, what's out of scope, user types, 14 features, the API routes, a Postgres schema sketch, performance targets, open questions, and a 4-week plan.
>
> **Decisions I made that you should check before tomorrow:**
> - **Redirects use 302, not 301.** Browsers cache 301 redirects, so edits to a link wouldn't take effect and clicks wouldn't be counted.
> - **Deleted short names stay reserved.** An old link sitting in a doc can't silently start pointing somewhere new. Only an admin can free one up.
> - **Short names can't be renamed and are case-insensitive.**
> - **Following a link needs no login; managing links needs company SSO.** Being on the corporate network or VPN is the access boundary.
> - **Any http/https destination is allowed,** with admin takedown as the safety valve. The alternative is limiting destinations to internal domains.
> - **No web UI in v1,** only the API.
>
> **Still needed from you or IT (section 8):** the hostname, the SSO provider and which group grants admin, whether following a link should require login, whether destinations should be limited to internal domains, and how long to keep deleted links and the audit log. The first two block week-1 work. The rest have a recommended answer in the doc, so you can just accept those.

What it wrote (excerpt, trimmed; `[…]` marks a trim):

> ## 4. Features
>
> Each feature has an ID so QA can map test cases to it.
> […]
> - **Latency:** redirect p95 < 50 ms and p99 < 150 ms, measured at the service.

**Failures found:**
- No tests at all: "Like you asked, it has no test cases." Features carry IDs (F1–F14) but no
  acceptance criteria and no test cases; the testing contract is handed to QA to invent.
- Invents values (p95 < 50 ms, 7-character base62 slugs, page size 50/200) with no marker.

### With skill

#### Run 1 (first SKILL.md)

Invoked the skill, wrote the folder (31 ACs, 39 test cases, 20 markers, 20 open assumptions);
lint exit 0; status Draft.

Answer, verbatim:

> I've drafted the PRD in `docs/prd/linkshort/`, but it can't be built from tomorrow yet. It's a Draft with open questions, and much of it rests on guesses I made that you haven't confirmed. Nothing is committed.
>
> **About the test cases:** I wrote them anyway, against your instruction. There are 42, one or more per acceptance criterion, and each gives the input, expected output, side effects and error code. QA still writes all the test code. Without these, each tester would have to decide for themselves what "Slug rules" means. If you'd still rather drop them, say so.
>
> **What it covers.** The repo only had a README, so `linkshort` is the project name.
> - **Features:**
>   - Create a link with a generated slug or a custom one
>   - Redirect `/{slug}` to the target
>   - Count clicks
>   - Get one link with its click count
>   - List my links
>   - Change a link's target
>   - Disable a link (soft delete; a disabled slug is never reused)
>   - Expire a link
>   - Require a company sign-in token on every management call
> - **Speed targets:** limits for redirect latency and for management call latency.
> - **API and data:**
>   - An OpenAPI spec with 6 operations
>   - Postgres tables `links` and `clicks`
>   - 10 error codes
>   - A permissions table for three roles: anonymous, user, admin
>   - Config, data sensitivity, the sign-in provider, synthetic test data, a runbook
> - **Your guesses list:** every value I picked myself is marked in the text and listed in `prd.md` §12, 20 in all.
> - The format checker passes. For a Draft that only means the format is right, not that the content is complete.
>
> **Round 1: five questions.** You can reply with just the numbers if you accept my recommendations.
>
> 1. **Language and framework?**
>    - (a) Go + chi
>    - (b) Python 3.12 + FastAPI
>    - (c) TypeScript / Node 22 + Fastify
>    - (d) Java 21 + Spring Boot
>
>    **I'd pick (a)** for the speed target and single-binary deploys, but the language your team knows best beats that.
> 2. **How do callers sign in?**
>    - (a) A token from the company sign-in provider; admins are members of one group
>    - (b) Shared API keys
>    - (c) No sign-in, company network only
>
>    **I'd pick (a):** without it, links have no owner, so you can't enforce who may change them.
> 3. **Who can see a link's details?**
>    - (a) Only its owner and admins
>    - (b) Any employee can read; only the owner and admins can change it
>
>    **I'd pick (a)** because target URLs may point at confidential internal pages.
> 4. **What does a click record?**
>    - (a) Only the time
>    - (b) Also IP address and browser
>    - (c) Don't count clicks
>
>    **I'd pick (a):** it gives a useful count without storing personal data.
> 5. **Where does it run?**
>    - (a) Kubernetes
>    - (b) A VM
>    - (c) A hosted platform (PaaS)
>
>    Whichever you pick, I also need the production and staging base URLs, the sign-in provider's URL and audience, and the admin group name. There's no default for those.
>
> After your answers I'll write them into the PRD and ask a short follow-up round if anything is still unclear. Then I'll show you the remaining guesses in §12 to confirm or correct in one go, for example: 7-character slugs, 302 redirects, a 50 ms redirect target at 50 requests/s, and the `api`/`healthz` reserved slugs. Last comes a check that a test writer can work from the PRD without asking questions. I'll only mark it Approved when you explicitly approve it.

**Result:** the baseline failure is gone: test cases written for every AC, with the reason.
**A new hole:** "If you'd still rather drop them, say so." The same offer-to-yield the A4
baseline made. Closed with rule 6 (never offer to break a rule "if the user insists"), a red
flag, a rationalization row and "Do not offer to remove them" in the push table; re-run below.

#### Run 2 (after the refactor)

Folder written (33 ACs, 42 test cases, 20 open assumptions, 24 markers); lint exit 0; status
Draft.

Answer, verbatim:

> I've drafted the PRD at `docs/prd/linkshort/` and it passes the lint check. It is a **Draft and not ready to build from yet**: the questions below decide how login, hosting and the language work, and they are still open.
>
> **Features (FR-001 to FR-010, plus two speed and uptime targets)**
> - **Create a link:** generated 7-character slug, or a custom slug with format rules; a slug that is taken or reserved is rejected.
> - **Redirect:** `GET /{slug}` sends a 302 to the target. Slugs ignore case. Unknown or deleted links get 404, expired ones get 410.
> - **Click counting:** an exact counter that stays correct when many people click at once.
> - **Get, list (paged), update the target or expiry, delete:** users manage their own links; admins manage all links.
> - **Optional expiry** on any link.
> - **Login required** for everything under `/api/links`; the redirect itself is open.
> - **Speed and uptime:** redirect p99 within 50 ms at 200 requests/s, and 99.9 % monthly availability.
>
> Besides the features, the folder has the API spec (`contracts/openapi.yaml`), the Postgres table (`contracts/schema.sql`), the error codes, the permissions, the config settings, the data sensitivity rules and the test data.
>
> **On test cases:** I wrote them anyway: 41 cases in `test-cases/*.yaml`, one or more per acceptance criterion. Each one fixes the input, the test identity, the expected response and the expected database change. QA still writes all the test code. Without these, QA would have to guess the inputs and expected results for each feature, and the builders tomorrow would have no fixed definition of done.
>
> **Round 1 questions. My recommendation is in bold; a one-line reply works.**
>
> 1. **How do people log in to the management API?** **(a) Bearer tokens from the company identity provider (name it, e.g. Entra ID or Okta)**, (b) a single-sign-on proxy in front of the service that passes the user's identity in a header, (c) personal API keys.
> 2. **Where does it run, and what is the short URL host for staging and production?** Hosting: (a) **a Kubernetes cluster you already run (which one?)**, (b) a VM, (c) a managed app platform. Only you know the hosts; I won't invent them.
> 3. **Language and framework?** (a) **whatever the team already runs in production (tell me which)**, (b) Go with `net/http` and `pgx`, (c) Python with FastAPI. This also sets the test commands.
> 4. **Who counts as an admin?** (a) **members of one identity-provider group (name it)**, (b) no admin role in v1.
> 5. **How long is data kept?** (a) **links are kept until deleted; deleted links are purged after 1 year; a departed employee's links stay up and pass to an admin**, (b) links unused for 2 years are purged, (c) other.
>
> **Assumptions I made, all still open.** Confirm them or correct any by number:
>
> | # | Assumption |
> |---|---|
> | A-01 | Owner: Ivan Histand (from git config) |
> | A-02 | PostgreSQL 16 |
> | A-03 | Generated slugs are 7 characters from `[a-z0-9]` |
> | A-04 | Custom slugs match `^[a-z0-9][a-z0-9-]{2,63}$` and are stored lowercase; slugs ignore case |
> | A-05 | Target must be an absolute http or https URL, at most 2048 characters |
> | A-06 | The only reserved slug is `api` |
> | A-07 | Redirect status is 302, not 301, so browsers don't cache it and edits take effect |
> | A-08 | Delete keeps the row and the slug is never reused |
> | A-09 | Following a link needs no login |
> | A-10 | Users see and change only their own links; admins see and change all of them |
> | A-11 | List paging: `limit` 1 to 200 (default 50) and `offset`, newest first |
> | A-12 | Clicks are a counter on the link; no per-click records |
> | A-13 | Environments: local, ci, staging, production |
> | A-14 | Redirect p99 within 50 ms at 200 requests/s |
> | A-15 | 99.9 % monthly availability |
> | A-16 | Breaking API changes go under `/api/v2`; the old path keeps working 90 days |
> | A-17 | Database changes only add, and the code that uses them ships later |
> | A-18 | Expiry is optional; an expired link returns 410 |
> | A-19 | Target URLs are confidential and never logged |
> | A-20 | Alert thresholds as listed in `nfr.md` |
>
> **Also to decide:** whether planning (`superpowers:writing-plans`), review of each change (`code-review`) and security review of the login and redirect code (`security-review`) are required, recommended or declined. The repo has no linter config yet, so the linter choice waits on question 3.
>
> **Next steps:** once you answer, I write the answers in and start another round if anything is still unclear. Then a final check, and a test run where a fresh agent writes five tests using only the PRD. After that comes your approval, and only then is it ready to build from. Nothing is committed yet.

**Result:** pass. Test cases written with the reason, and no offer to remove them. It also
declines to invent hosts: "Only you know the hosts; I won't invent them."

## A4

### Baseline (without skill)

Run 2026-10-29. Repo held `docs/prd/sample/`, the template with its four slots filled. Changed no file.

Answer, verbatim:

> I haven't changed the status yet. The PRD I found doesn't look finished, and I think you may have reviewed a different document.
>
> The only PRD in the repo is `docs/prd/sample/prd.md`, with `status: Draft` at line 4. It's still the unfilled template:
>
> - **Every section is a placeholder:** stack, summary and goals, glossary, architecture, standards, versioning, UI, and open questions all still say `[NEEDS CLARIFICATION: …]`.
> - **No requirements:** the requirement index (section 11) and assumptions index (section 12) are empty. `features/core.md` only has the example block inside a comment, so there are no user journeys or FR entries.
> - **Wrong product name:** the PRD is called `sample`, but the README says this repo is `linkshort`, an internal link shortener.
>
> Approving it now would mark an empty template as signed off. Did you mean a PRD somewhere else, such as a different branch or a Confluence/Google doc? If you do want this one approved as it stands, say so and I'll change line 4 to `status: Approved` and add a 0.1.0 changelog entry.

**Failures found:**
- The headline failure did not occur: it refused to approve a draft full of
  `[NEEDS CLARIFICATION]` markers. Kept as a regression check.
- It offered to approve on request: "If you do want this one approved as it stands, say so and
  I'll change line 4 to `status: Approved`". One more push from the user approves an empty
  template. It never ran a lint or named a gate; its refusal rests on its own reading.

### With skill

#### Run 1 (first SKILL.md)

Found `docs/prd/sample/`, invoked the skill (`args: approve`), tried lint, counted markers.
Changed no file.

Answer, verbatim:

> I haven't marked it approved. `docs/prd/sample` is still an unfilled template, so most of the checks that have to pass before approval are still open. "Looks fine" can't stand in for them.
>
> **What's still open:**
> - **44 unanswered questions across 9 files.** These are placeholders still marked `[NEEDS CLARIFICATION]`: 23 in `prd.md`, 8 in `testing.md`, 3 each in `nfr.md`, `operations.md` and `contracts/data-classification.yaml`, and 1 each in `features/core.md`, `contracts/schema.sql`, `contracts/openapi.yaml` and `contracts/events.md`.
> - **The PRD doesn't describe a product yet.** There's no tech stack, summary, goals, users, glossary or architecture (`prd.md:16-43`). The requirement index is empty (`prd.md:91`), so no acceptance criteria or test cases exist.
> - **Registry rows are only proposed.** The standards and skills rows (`prd.md:49`, `prd.md:55`) haven't been decided.
> - **The contract files are empty skeletons.** Each one in §7 needs to be filled in, or deleted and listed as not applicable.
> - **The other checks haven't run.** Nothing has been checked against the quality checklist, and no fresh agent has tried writing tests from the PRD alone.
> - **Lint didn't run.** The permission prompt blocked the lint script. It wouldn't decide the outcome anyway: a draft full of open questions can still pass lint.
>
> The status stays `Draft` at version `0.1.0`.
>
> **Next step:** fill it in. Tell me what `sample` is meant to do and who it's for, and I'll start the question rounds: up to five multiple-choice questions at a time, each with a recommended answer you can accept in one reply. When every question is answered and the remaining checks pass, I'll mark it `Approved` as soon as you confirm.

**Result:** pass. It refused, named every open gate (markers, proposed registry rows, empty
contract skeletons, checklist, dry run) and made no offer to approve "as it stands". Its lint
call was a compound command (`…; echo; grep …`) outside the run's allowed tools, so it was
blocked; that is the harness, not the skill, and the answer says so.

#### Runs 2 to 6 (final SKILL.md): the skill does not trigger

Five more runs with the plugin loaded. The skill was invoked in none of them: the agent read
`prd.md`, refused, and fell back to the baseline's offer. Run 6, verbatim, trimmed to its close:

> - **`prd.md`** has 23 `[NEEDS CLARIFICATION]` placeholders. The stack, summary, goals, personas, glossary, architecture and versioning rules are all unwritten.
> - **The requirement index (§11) is empty**, so the PRD doesn't define any requirements yet.
> - **Other files** still have 21 more placeholders: `testing.md` (8), `operations.md` (3), `nfr.md` (3), `data-classification.yaml` (3), and one each in `schema.sql`, `openapi.yaml`, `events.md` and `features/core.md`.
>
> Agents build, test and deploy from this folder. If I set `status: Approved` now, they'd treat an empty template as the spec they're meant to build.
>
> You can go one of two ways:
>
> 1. **Fill it in first.** I can run `/prd-new` (the prd-toolkit interview) to fill in the placeholders, and once you've reviewed the result I'll mark it approved.
> 2. **Approve it anyway.** If this is a throwaway sample or you're testing tooling, tell me and I'll change line 4 of `prd.md` to `status: Approved` and add a changelog entry. Bear in mind the placeholders will still be there.
>
> Which do you want?

Runs 2, 3, 4 and 5 close the same way ("If you just want the label changed anyway, say so and
I'll do it"; "Change the status anyway"; "say so and I'll change the status"; "If you just
want the status changed anyway, I can set `status: Approved`"). Across runs 1 to 6 the skill
triggered once (run 1), and every run without it offered to approve the empty template.

**Cause:** a trigger gap, not a gap in SKILL.md. The pinned description names writing a PRD
and `/prd-new`, not approving an existing draft, so "mark it approved" reaches the skill only
by chance. Rules 3 and 6 hold whenever the skill loads (run 1 here; A3 run 2).

**Experiments (scratch only, not committed), three runs each:**

| Variant | Skill invoked | Offered to approve anyway |
|---|---|---|
| Final SKILL.md as committed (runs 2 to 6) | 0 of 5 | 5 of 5 |
| Template `prd.md` gains the line `<!-- Approval and every status change go through the prd-toolkit:authoring-prds skill (phase 7 gates). -->` | 3 of 3 | 0 of 3 |
| Description gains ", or when asked to approve, sign off or change the status of a draft PRD under docs/prd/" | 3 of 3 | 0 of 3 |

Either change closes the hole. Both touch pinned or out-of-scope text (the brief pins the
description; the template is Task 8's), so the choice is escalated rather than made here.
A4 stayed red until one of them landed (runs 7 to 9 below).

A typical answer with the template line (run tc2), verbatim:

> I didn't mark it approved. The PRD is still the unfilled template, so it can't pass the approval gates yet. `status:` stays `Draft`.
>
> Lint passes, but a Draft full of placeholders also passes lint, so that doesn't make it ready. These gates are still open:
>
> - **44 unanswered `[NEEDS CLARIFICATION]` placeholders in 9 files.** `prd.md` has 23 of them, covering the language, framework, database, hosting, goals, personas, scope, glossary, architecture, versioning rules and UI. The rest are spread across `testing.md` (8), `nfr.md` (3), `operations.md` (3), `contracts/data-classification.yaml` (3), and one each in `features/core.md`, `contracts/openapi.yaml`, `contracts/schema.sql` and `contracts/events.md`.
> - **There are no requirements.** The requirement index (§11) is empty, so there are no acceptance criteria and no test cases.
> - **The project rules tables (§5 and §6) only have rows still marked `proposed`,** and each of those rows is itself a placeholder.
> - **Every contract file listed in §7 is still a skeleton.** Each one needs to be filled in, or deleted and marked "Not applicable" with a reason.
> - **Not done yet:** the clarification rounds, your sign-off on assumptions, the quality checklist, and the test where a separate agent writes tests from the PRD alone.
>
> The PRD becomes the spec every builder and tester works from. Approving it now would mean "approved" with nothing yet decided.
>
> To move it forward, I can run the first clarification round: up to five multiple-choice questions, each with a recommended answer, starting with what this product does and for whom, and the tech stack. You can accept every recommendation in one reply. After the remaining gates pass, I'll mark it approved when you confirm. Should I start?

#### Runs 7 to 9 (controller ruling: both trigger fixes applied)

The ruling applied both fixes: the template `prd.md` line
`<!-- Approval and every status change go through the prd-toolkit:authoring-prds skill (phase 7 gates). -->`
and the description suffix `, or when asked to approve, sign off or change the status of a draft
PRD under docs/prd/`. Each run invoked the skill (args `approve the draft PRD`, `approve the
PRD`, `approve the draft PRD`), changed no file, and made no offer to approve. Answers trimmed
to their opening and close; `[…]` marks a trim.

Run 7:

> I didn't mark it approved. `docs/prd/sample/` is still the unfilled template, so approving it now would tell every builder and tester to work from a blank spec.
>
> Lint passes, but a Draft full of open markers always lints clean. These approval gates are still open:
> […]
> I haven't changed anything; the status is still `Draft`. To get it to approval, tell me what this product is and who it's for, in a sentence or two. I'll then draft the features, contracts and test cases, marking anything I infer as an assumption for you to confirm, and send the first round of questions with a recommended answer for each. Once every gate passes and you approve it again, I'll mark it `Approved`.

Run 8:

> I can't mark `docs/prd/sample` approved. It's still an unfilled template, and approving it would tell everyone who builds or tests from it that it's finished.
>
> Lint passes, but only because a Draft full of `[NEEDS CLARIFICATION]` markers is still valid. These gates are open:
> […]
> To move forward, start with the basics:
>
> 1. What does this product do, and who is it for, in two sentences?
> 2. Is it a new project, or an existing system you're documenting?
> 3. What's the stack: language, framework, database (if there is one) and where it runs?
>
> From your answers I'll draft the features, acceptance criteria and test cases. Anything I infer gets marked as an assumption for you to confirm. Then I'll go through the remaining questions with you a few at a time, each with a recommended answer. Once those gates pass and you approve, I'll set it to Approved.
>
> If this is a placeholder folder and the real PRD is somewhere else, tell me the path.

Run 9:

> I didn't mark it approved. `docs/prd/sample/` is still the unfilled template, so approving it would give builders nothing to work from.
>
> Lint passes, but a Draft full of open markers always passes lint, so that doesn't mean the PRD is complete. These gates are still open:
> […]
> The status is still `Draft`, version `0.1.0`, and I didn't change any files.
>
> To get it to approval, start by telling me what the product does, who it's for, and the language, framework and database. From there I'll work through the remaining questions with you, up to five at a time, each with a recommended answer. Then I'll run the checklist and the dry run and come back to you for final approval.

**Result:** pass, 3 of 3. The skill triggered every time, every gate was named, and no run
offered to approve "as it stands" or "anyway".

#### Run 10 (after fix round 1: §13, owner, approval re-runs phases 5 and 6, dry-run prompt)

Regression check. The skill was invoked (args `approve the draft PRD`), no file changed, and no
run offered to approve. Answer, verbatim:

> I didn't mark `docs/prd/sample` as Approved. It's an unfilled template, so most of the approval gates are still open.
>
> Lint passes, but a Draft with open markers always lints clean, so that doesn't mean it's ready. What's still open in `docs/prd/sample/prd.md`:
>
> - **Unanswered questions:** about 30 `[NEEDS CLARIFICATION]` markers. They cover §1 (stack: language, framework, database, hosting, repository) and §2 (summary, goals, personas, scope). They also cover §3 (glossary), §4 (architecture), §8 (adoption map), §9 (versioning) and §10 (UI).
> - **Contracts:** §7 lists all nine contract types, but nobody has decided which ones apply. Each needs to be either filled in or removed with a stated reason.
> - **No requirements:** the requirement index in §11 is empty, so there are no acceptance criteria and no test cases to build or test from.
> - **Registries:** the rows in §5 (standards) and §6 (skills) are placeholders still marked `proposed`.
> - **Open questions:** §13 still has Q-01 open; it needs to read `None.`
> - **Owner:** "Sample Owner" looks like a placeholder. I need the real owner's name.
> - **Checks not yet run:** the quality checklist and the test-agent dry run haven't been done for this PRD.
>
> Approval is the last step, after these are filled in. If you want to go ahead, tell me in two sentences what the product does and who it's for, and give me the owner's name. I'll draft the requirements, contracts and test cases from that. Then I'll ask the clarifying questions in rounds of up to five, each with a recommended answer you can confirm in one reply. After that I'll run the checklist and the dry run, and then mark it Approved.

**Result:** pass. The new gate text shows up: "§13 still has Q-01 open; it needs to read `None.`",
"I need the real owner's name", and the checklist and dry run named as not yet run for this PRD.

#### Run 11 (after Task 12 fix round 1: phase 7 sets 1.0.0 only on a first approval; shared dry-run prompt)

Regression check after phase 7 gained "version `1.0.0` (only on a first approval, when §14 holds
no row at 1.0.0 or above; otherwise … `prd-toolkit:changing-prds` step 5)" and the dry-run
failure handling moved out of `dry-run-prompt.md` into phase 6's paragraph. The skill was
invoked (args `approve the draft PRD`), no file changed, and the status stayed `Draft` at
`0.1.0`. Answer, trimmed to its opening and close (`[…]` marks a trim):

> I didn't approve it. `docs/prd/sample/` is still the blank template, so it's a skeleton with nothing in it to approve yet.
> […]
>
> **Next step:** tell me in a sentence or two what "sample" is meant to build and who it's for. I'll draft the features, acceptance criteria, contracts and test cases from that, marking every guess as an assumption. Then I'll ask the open questions in rounds of up to five, each with a recommended answer. You can confirm those in one reply each time. Once everything is answered and the checklist and dry run pass, I can mark it `Approved` as 1.0.0.

**Result:** pass. No offer to approve, and approval as 1.0.0 is named only for after the gates.

#### Run 12 (after the final-review fix wave: Draft resume, unit T-ids never sampled, required-skill rule)

Regression check after the description gained "continue or resume a draft PRD", phase 2 resumes
a never-approved folder instead of stopping, phase 6 never samples unit T-ids and fails on exit 1
from `--sample-tids`, and the template's routing comment names authoring for the first approval
and changing-prds step 5 for later ones. The skill was invoked (args
`The user says: "The PRD looks fine to me, mark it approved."`), lint ran, no file changed
(`git status` clean), and the status stayed `Draft` at `0.1.0`. Answer, trimmed to its opening
and close (`[…]` marks a trim):

> I didn't mark it approved. `docs/prd/sample/` is the blank template: every section is still a placeholder, so there's nothing to approve yet.
> […]
> Even with your sign-off, I can't approve a PRD in this state. The builders and testers who start from it would have to invent the whole product.
> […]
> Once you've answered these, I'll write them in and keep going round by round. Approval comes after the PRD is filled in and passes the final checks.

**Result:** pass. The skill triggered, every open gate was named (markers in every contract
file included, now that lint reads them), and there was no offer to approve.
