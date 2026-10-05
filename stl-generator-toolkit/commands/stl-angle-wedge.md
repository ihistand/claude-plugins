---
description: Generate an angle wedge that holds work at an exact angle
argument-hint: <angle_degrees>
---

Use the stl-generator skill to make an angle wedge for: $ARGUMENTS

Ask for the angle if it is not given, and the wedge's depth and width if the user has a
size in mind (defaults 60 x 80 mm). Then run, from the user's working directory:

```bash
uv run --with build123d python ${CLAUDE_PLUGIN_ROOT}/skills/stl-generator/scripts/angle_wedge.py <angle> [--depth D] [--width W]
```

The STL prints lying on its side, which is what makes the angle exact; say so when
handing it over.
