# Extra clarify questions for a document PRD

Ask these in the authoring interview, after the usual ones. Each answer goes into the document's
`outline` entry or its requirements; an unknown stays a `[NEEDS CLARIFICATION]` marker.

- **Audience.** Who reads it, and in what situation (first day, an incident at night, an audit)?
- **Prior knowledge.** What does the reader already know, and which terms must the document explain?
- **Reading level.** Plain language for non-specialists, or the vocabulary of the field?
- **Tone.** Formal, friendly, instructional, neutral?
- **Length.** A target word range, and whether a reader scans it or reads it through.
- **Format conventions.** Heading levels, numbered steps, tables, admonitions, code blocks, link style.
- **Output language.** The language of the document, when it differs from the PRD's `language:`.
- **Parsing standard.** Ask it up front. The checks parse each document as CommonMark 0.31.2 after NFC
  normalization, and a section is a level-2 heading whose text equals a `sections` entry, once each.
  If the author wants another standard (another Markdown flavour, sections at level 3), write it into
  the Harness Assertions slot in place of the pack's default.
