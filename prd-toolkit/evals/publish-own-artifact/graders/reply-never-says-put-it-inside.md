---
type: regex
pattern: '(?:(?:^|[.:;!?]\s+|\n\s*(?:[-*]\s+)?(?:\*\*[^*\n]+\*\*:?\s*)?|, (?:then )?|\byou(?:''ll| will)? (?:can|could|may|need to|have to|should) |\bto (?:publish|get|finish) it[^,\n]*, )(?:upload|add|put|drop|rename|place|copy|attach)\b[^.\n]*?(?:prd\.html|design artifact|the artifact(?! tool)|your artifact|that artifact)|\bname it\s+`?prd\.html|\bunder the name\s+`?prd\.html)'
flags: i
match: not_contains
target: last_message
---

The reply never tells the owner to put the page inside the design artifact: no sentence, bullet, ", " clause or
"you can / you'll need to" clause that opens with upload, add, put, drop, rename, place, copy or attach and goes on
to `prd.html`, the design artifact, "the artifact" (not "the Artifact tool") or "that artifact", and no "name it
`prd.html`" or "under the name `prd.html`". JavaScript regex (the runner's), so `flags: i`, never an inline `(?i)`. RED's three replies each held one ("To publish it, upload that
file to the artifact as `prd.html`"); a negation ("I wouldn't add the page to the design artifact") does not match.
