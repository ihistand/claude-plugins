# Clarify categories

Credit: the clarify-by-category approach adapts GitHub Spec Kit (MIT). The categories and wording are original to prd-toolkit.

Authoring phase 3 runs rounds of questions until the PRD is unambiguous. Score each category,
then ask about the weakest.

## The twelve categories

1. Stack: language, framework, runtime, hosting, versions.
2. Data model: tables, keys, nullability, defaults, relationships.
3. Flows: the happy path of each user journey and feature, step by step.
4. Error and empty states: what the user sees and what the system does when something fails or nothing exists.
5. Edge cases: duplicates, limits, concurrency, time zones, partial input.
6. Integrations: third-party services, auth, rate limits, failure and mock behaviour.
7. Permissions: roles, operations, row-level rules, test identities.
8. Configuration: settings, flags and their values per environment.
9. Data classification: sensitivity, retention, deletion, masking.
10. NFR bounds: latency, throughput, availability, size, each as a number with a unit.
11. Terminology: glossary terms, banned synonyms, one word per concept.
12. Done signals: how the owner knows each requirement is met; acceptance steps and who signs off.

## Scoring

Give every category one score:

| Score | Meaning |
|---|---|
| Clear | The PRD answers it with specifics, or an `[ASSUMPTION A-nn: …]` stands in for each fact still unknown; a tester needs to ask nothing |
| Partial | Some answers exist, but a gap remains that is neither answered nor covered by an assumption |
| Missing | Nothing, or only a `[NEEDS CLARIFICATION: …]` marker |

Exit phase 3 when no `[NEEDS CLARIFICATION]` marker remains and every category is Clear. A
category whose remaining gaps are all covered by `[ASSUMPTION A-nn: …]` markers counts as Clear
for this gate. Phase 4 then confirms or corrects every assumption with the user, so none reaches
approval unconfirmed.

## A round

1. Ask at most five questions. Rank candidates by impact times uncertainty: a wrong guess that would change the data model or a contract outranks a wording choice.
2. Make each question multiple choice, two to four options, with your recommended answer marked and one line of reasoning.
3. Allow a free-text answer for the user who has a different option.
4. Write each answer into the PRD immediately, in the section it belongs to. Remove the marker or assumption it settles, and update the assumptions index.
5. Re-score the categories. Start another round if any is not Clear. The total number of rounds has no cap.

Ask nothing the repo, its notes or a lookup can answer. Ask the user only what only the user knows.
