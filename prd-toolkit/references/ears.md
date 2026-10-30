# EARS acceptance criteria

Credit: the EARS pattern set follows the usage in cc-sdd (MIT). The wording here is original.

EARS (Easy Approach to Requirements Syntax) gives every acceptance criterion one of five shapes.
Each shape fixes the order of trigger, condition and response, so a tester reads one observable
result out of it.

| Pattern | Form | Use for |
|---|---|---|
| Ubiquitous | The `<system>` shall `<response>`. | Behaviour that always holds |
| Event | When `<trigger>`, the `<system>` shall `<response>`. | A response to one event |
| State | While `<state>`, the `<system>` shall `<response>`. | Behaviour that holds during a state |
| Unwanted | If `<condition>`, then the `<system>` shall `<response>`. | Errors and failures |
| Optional | Where `<feature is present>`, the `<system>` shall `<response>`. | Behaviour tied to a configurable feature |

Examples in the FR-012 domain, the duplicate order import:

- Ubiquitous: AC-012.1 The importer shall store `order_key` unchanged from the import file.
- Event: AC-012.2 When an imported row's `order_key` already exists, the importer shall skip the row and write one `duplicate` entry to `import_log`.
- State: AC-012.3 While an import is running, the importer shall reject a second import of the same file.
- Unwanted: AC-012.4 If the import file is empty, then the importer shall finish with status `empty` and insert no rows.
- Optional: AC-012.5 Where the `IMPORT_DRY_RUN` setting is on, the importer shall report counts and write no rows.

Combine patterns when a criterion needs both (`While` plus `When`), but keep one response per
criterion so one test case proves it.

## What the `ac-ears` rule checks

Every `- AC-nnn.n` item must:

- start with `When`, `While`, `If` or `Where`, or with `The <thing> shall`; and
- contain the word `shall`.

The rule does not check that the response is observable or measurable. Judge that with the
quality checklist ([quality-checklist.md](quality-checklist.md)). The `vague-word` rule separately
rejects words such as "fast", "secure" or "user-friendly" in an AC or an NFR line, but only
when that line has no number; digits inside IDs such as `AC-004.1` do not count. A number on the
line silences the rule, so "fast, within 200 ms" passes lint; the checklist still asks whether
the bound is one a test can fail. Write the number: "within 200 ms".

See [prd-format.md](prd-format.md) for where ACs sit in a requirement block.
