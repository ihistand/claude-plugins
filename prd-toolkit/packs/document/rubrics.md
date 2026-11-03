# Writing rubrics for documents

A judged case scores a document against a rubric. Write each rubric item so a grader can prove it
with a quote from the document.

- **One observable claim per item.** "Each step in Install names one action the reader performs", not
  "Install is easy to follow and complete".
- **Name what it is about:** the section, the term or the reader action. "First run shows the command
  and the output the reader will see" points at a place a quote can come from.
- **No judgement words.** Do not write "is clear", "reads well", "is good", "is helpful" or "is
  appropriate". If a reader could disagree about what the item means, split it or sharpen it.
- **3 to 8 items.** Fewer leaves the case too coarse; more makes one failing run hard to read.
- **Threshold.** The share of items that must pass. Use 1.0 only when every item is a hard
  requirement. A lower threshold (0.67 to 0.8) tolerates one soft item failing in a run; the median of
  `runs:` runs decides, so keep `runs:` at 3 or more for any threshold below 1.0.
- **Language.** Write the items in the PRD's `language:`.
- **A script check beats a rubric item.** Sections present in order, terms used, word count in range
  and links that resolve belong in the `checks` level, not here.
