---
description: Generate precision spacing or setup blocks, single or a matched set
argument-hint: <height_mm> | --set h1,h2,...
---

Use the stl-generator skill to make spacing blocks for: $ARGUMENTS

Ask for the height (or the set of heights) if not given. Then run, from the user's
working directory:

```bash
uv run --with build123d python ${CLAUDE_PLUGIN_ROOT}/skills/stl-generator/scripts/spacing_block.py <height> [--width W] [--depth D]
uv run --with build123d python ${CLAUDE_PLUGIN_ROOT}/skills/stl-generator/scripts/spacing_block.py --set 5,10,15,20
```

Pass on any layer-height warning the script prints, and suggest 100% infill: these
blocks take clamping pressure.
