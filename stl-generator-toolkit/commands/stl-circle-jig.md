---
description: Generate a router circle-cutting trammel (discs and rings, e.g. lampshade rings)
argument-hint: <outer_mm> [inner_mm]
---

Use the stl-generator skill to make a circle-cutting trammel for: $ARGUMENTS

Before generating, ask for anything not given: the outer (and, for a ring, inner)
diameter, the router bit's cutting diameter, and the router sub-base screw pattern
(bolt-circle diameter and screw count). Then run, from the user's working directory:

```bash
uv run --with build123d python ${CLAUDE_PLUGIN_ROOT}/skills/stl-generator/scripts/circle_cutting_jig.py <outer> [inner] --bit <bit_mm> --mount <BC>:<N>
```

Hand over what the skill's "Handing over the result" section lists, plus the cut
order the script prints (outer edge first, inner edge last).
