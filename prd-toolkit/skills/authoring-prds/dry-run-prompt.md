# Dry-run prompt

Shared by `authoring-prds` (phase 6) and `changing-prds` (step 4). Each skill says what to do
when the dry run fails.

Dispatch a fresh general-purpose subagent (Agent tool) with this prompt. Fill the three slots.
`<SCRATCH_DIR>` is a new, empty subdirectory of the scratch directory for every run, named by
timestamp (for example `<scratchpad>/prd-dry-run-20261029T153000`), so no run sees an earlier
run's tests. `<T_IDS>` never holds a unit T-id.
Give it nothing else: no summary of the PRD, no hints, no answers. In 0.1 the read-only
restriction is an instruction, not enforced, so check its report for files read outside the folder.

```
You are a black-box tester. You have never seen this system's code and you must not look for it.

You may read ONLY files under <PRD_DIR>/ (for example docs/prd/linkshort/). Do not read, list or
search anything else in the repository: no source, no tests, no README, no git history.
Facts you hold from your own context (CLAUDE.md, memory, environment notes) are outside the PRD
folder. Do not use them; if you need one, record it under QUESTIONS.

Write a real, runnable test for each of these T-ids, in the harness that <PRD_DIR>/testing.md
names for the case's level:

<T_IDS, one per line>

Write the tests to <SCRATCH_DIR>/, never into the repository. Read nothing else in the scratch
area: earlier runs' tests are not yours.

Work only from the PRD: the test case in <PRD_DIR>/test-cases/, the AC it names, and the
contracts, fixtures, environments and identities it references. Whenever the PRD does not tell
you something you need (a URL, a payload field, an error code, a fixture's contents, a harness
command, an expected value), do not guess and do not look elsewhere: record the question and
carry on with the next element.

Test helpers that <PRD_DIR>/testing.md names (fixtures, clients, loaders, page objects) may not
exist yet. If they do not exist yet, write them yourself, in <SCRATCH_DIR>/, to match what
testing.md says about them. A detail testing.md leaves open about a helper's own internals (a
method signature, a return value, a default such as following redirects) is yours to choose:
list it under HARNESS CHOICES, not QUESTIONS. Anything else the PRD does not tell you is a
question: behaviour, payloads, status codes, error codes, fixture contents, environments,
identities, or a convention testing.md should state.

Report, in this order:
1. QUESTIONS: every question you had to ask, one per line, each naming the T-id and the file
   that should have answered it. Write "none" only if you had no question at all.
2. TESTS: one line per T-id above, `<T-id>: <path of the test you wrote>`. A T-id you could not
   write a test for gets `<T-id>: none` and its reasons under QUESTIONS.
3. HARNESS CHOICES: every helper you wrote and each internal detail you chose for it, one per
   line. Write "none" if you wrote no helper.
4. FILES READ: every path you opened, listed or searched.
```

The dry run passes only when QUESTIONS is `none`, TESTS has one path for every T-id in the
slot, and every path under FILES READ is inside `<PRD_DIR>/`. Anything else fails it. Read
HARNESS CHOICES too: a choice that contradicts testing.md, or one that changes what a test
asserts, is a question in disguise and fails the run. The rest are the tester's to make; the
builder's harness may make them differently without changing any test case.
