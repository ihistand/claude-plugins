# Phase 6 dry-run prompt

Dispatch a fresh general-purpose subagent (Agent tool) with this prompt. Fill the three slots.
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

Write the tests to <SCRATCH_DIR>/, never into the repository.

Work only from the PRD: the test case in <PRD_DIR>/test-cases/, the AC it names, and the
contracts, fixtures, environments and identities it references. Whenever the PRD does not tell
you something you need (a URL, a payload field, an error code, a fixture's contents, a harness
command, an expected value), do not guess and do not look elsewhere: record the question and
carry on with the next element.

Report, in this order:
1. QUESTIONS: every question you had to ask, one per line, each naming the T-id and the file
   that should have answered it. Write "none" only if you had no question at all.
2. TESTS: one line per T-id above, `<T-id>: <path of the test you wrote>`. A T-id you could not
   write a test for gets `<T-id>: none` and its reasons under QUESTIONS.
3. FILES READ: every path you opened, listed or searched.
```

The dry run passes only when QUESTIONS is `none`, TESTS has one path for every sampled T-id,
and every path under FILES READ is inside `<PRD_DIR>/`. Anything else fails it. Turn each
question into a `[NEEDS CLARIFICATION: …]` marker in the file it names and return to phase 3.
