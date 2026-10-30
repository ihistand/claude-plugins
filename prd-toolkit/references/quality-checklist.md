# Quality checklist

Credit: the checklist-as-unit-tests idea adapts GitHub Spec Kit (MIT). Assumptions and glossary practice follows BMAD-METHOD (MIT). The questions are original.

Run this after `prd_lint.py` exits 0 (authoring phase 5). Lint checks structure; these checks need
judgement. Answer each with yes or no. A "no" is a gap: fix it, then re-run lint.

## Requirements

- [ ] Is every AC testable by one observable result (one response, one state change), with no "and also"?
- [ ] Does no AC contradict another, in the same requirement or across features?
- [ ] Does each AC name a number, state or message a tester can compare against, rather than an adjective?
- [ ] Does every NFR carry a bound that a test can fail?

## Data and contracts

- [ ] Does every column state its type, nullability and default (see `schema` in [contract-types.md](contract-types.md))?
- [ ] Does every operation state its auth scheme, the role that may call it, and a fully typed request?
- [ ] Does every operation that changes state say whether a retry is safe (idempotency)?
- [ ] Does every error have a user-facing message a person could act on, without reading logs?
- [ ] Does every dependency have a mock, and does the PRD say tests never call production?
- [ ] Does every allow cell in `permissions.yaml` have a test, as well as every deny cell?
- [ ] Does every test case that depends on something outside its contracts (a component contract, an architecture fact, a Harness slot) cite it in `refs:`?

## Flows and people

- [ ] Does every flow have its empty state and its failure state?
- [ ] Do the personas in the Summary map to user journeys, and every journey to at least one FR?
- [ ] Does each journey end in a result the persona can observe?
- [ ] Does every acceptance case assert only what the signer can observe, create fresh data on every run where its environment keeps data, have a step that observes each `expect` item, and name a person in `signoff`?

## Scope and honesty

- [ ] Is Out of scope explicit, so a builder knows what to refuse?
- [ ] Does each assumption name who confirms it, and has the user confirmed it?
- [ ] Does the glossary give one term per concept, with the banned synonyms listed?
- [ ] Could a tester who has never seen the code write the tests from this folder alone?

The last question is the dry run's job (phase 6). Treat its questions as gaps.
