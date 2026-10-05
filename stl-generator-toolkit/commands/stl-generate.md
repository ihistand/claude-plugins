---
description: Design a custom 3D-printable woodworking jig or fixture and export the STL
argument-hint: <what the jig should do>
---

Use the stl-generator skill to design: $ARGUMENTS

If one of its ready scripts fits (circle-cutting trammel, angle wedge, spacing
blocks), use that. Otherwise follow the skill's "Custom jigs" section: build123d,
`export_checked` from `${CLAUDE_PLUGIN_ROOT}/skills/stl-generator/scripts/printcheck.py`
(copied next to the new script), and verify the part by measuring it before handing it over.
