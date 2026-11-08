# prd-toolkit 0.8.5: deploy and pack fixes from the first private-pack loop — backlog

> **Date:** 2026-11-07
> **Author:** Ivan Histand & Claude Code
> **Status:** Backlog, not designed. Each item becomes a section and plan tasks in 0.8.5's own
> brainstorm, or moves to a later release.
> **Extends:** `2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md` and the specs it extends, under
> `2026-11-03-prd-toolkit-0.8-umbrella.md`.
> **Needs:** 0.8.4 merged.
>
> **Revisions.**
> - Created (owner, 2026-11-07): items 1 to 6 were the 0.8.4 spec's section 16 (PR #19), recorded on
>   2026-11-05 for 0.8.3; 0.8.4 took the small fixes instead and moved these here. Items 7 and 8 are
>   later-release candidates from the same loop.
> - Item 9 (owner, 2026-11-08): drawing the mermaid diagram, from the 0.8.4 proof.

## 1. Backlog

The owner put items 1 to 6 on the backlog on 2026-11-05. They come from the first full change, build
and deploy loop on a private pack, where a service's own UI does part of each deploy, and from the
pack's first releases.

1. **Human steps done in one pass.** The owner did three consecutive human steps in one UI
   session, before the run asked for the first. The run still asked for each reply in turn, which
   took three extra round-trips. `prd_deploy.py confirm` could take a range of consecutive human
   steps when the owner's reply names each one.
2. **An error found mid-run.** Recording an `errors.md` entry during a run moves HEAD, and a
   moved HEAD blocks `resume`, so the entry had to wait for the close. `prd_error.py new` could
   leave its write uncommitted while a run is open, to be committed with the run's close.
3. **A `tests` step's timeout.** A live suite took 609 seconds against the 600-second default,
   so every `run` and `resume` needed `--timeout`. A `tests` step could declare its own timeout in
   the runbook, or `prd_deploy.py` could read one from testing.md's Levels.
4. **A close on the wrong branch.** The close commit lands on whatever branch ran the deploy.
   Where deploying means merging to an environment's branch and promoting in a UI, the close
   still needs a second push. `prd_deploy.py` could report `the close is on <branch>, not
   <the environment's branch>`.
5. **A Check that `prints` a line with a SHA.** A runbook Check's `prints` must match a whole
   output line exactly (`prdlint/deploy.py`). A check whose output carries a commit SHA or
   another changing value cannot use it, so such Checks fall back to the exit code alone.
   `prints` could take a prefix or a regular expression.
6. **A pack bump forces a PRD patch.** §1's `Pack:` line, or an area's `Target:` line, names an
   exact pack version, and `prd_hooks.py install` refuses a vendored pack whose version differs.
   So every pack release, even a fix that changes nothing the area relies on, needs a
   `/prd-change` at the next re-vendor just to move the line. The install could offer that edit
   as a ready-made patch for the owner to approve. A compatible-range declaration in the pack is
   the other way, but it lets an area run under a pack version it was never checked against.
7. **STALE judged by the cited line.** `prd_context.py` could judge a `Source:` region STALE by
   whether the cited line's text still stands, and scope its exit to the `--req` IDs.
8. **SOURCES lines inside the builder's hunks.** `prd_build_check.py --diff` could check that each
   SOURCES line of the builder's report falls inside a hunk of the round's diff.
9. **Draw the mermaid diagram.** 0.8.4 renders a mermaid fence as `<pre class="mermaid">`, expecting
   the Artifact viewer to draw it; the 0.8.4 proof (2026-11-08) found it shows the source, as a
   plain browser does. The owner put this here on 2026-11-08. Ways to weigh: render the diagram to
   inline SVG at publish time (a renderer dependency), or let the page load mermaid (it then loads
   something, which the page's "loads nothing" rule and its test refuse).
