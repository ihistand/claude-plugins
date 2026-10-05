# STL Generator Toolkit

Generate 3D-printable STL files for woodworking jigs and fixtures with
[build123d](https://github.com/gumyr/build123d). Ships the **stl-generator** skill,
tested ready-made scripts, and a print-readiness check that refuses an STL that would
misprint (a part floating above the bed, an invalid shape, a part too big for the bed).

The skill is a copy of the canonical one in
[ihistand/claude-skills](https://github.com/ihistand/claude-skills/tree/main/stl-generator),
synced by `scripts/sync-skills.sh`. Its `SKILL.md` and `references/` hold the design
rules, clearances, and build123d patterns.

## What's included

| Command | Makes |
|---|---|
| `/stl-circle-jig <outer> [inner]` | A router circle-cutting trammel for discs and rings (lampshade rings, round frames). Pivot holes are offset for the bit so circles come out at the size asked for; the plate takes your router's sub-base screw pattern. |
| `/stl-angle-wedge <angle>` | An angle wedge at an exact angle, printed on its side so the slope is traced in XY rather than stair-stepped by layers. |
| `/stl-spacing-block <height>` or `--set 5,10,15,20` | Spacing and setup blocks with flat measuring faces, engraved labels, and finger scallops; sets lay out to fit the bed. |
| `/stl-generate <description>` | Any custom jig: uses a ready script when one fits, otherwise designs one in build123d. |

The skill also triggers on its own when you ask for a jig, without a slash command.

## Requirements

- [uv](https://docs.astral.sh/uv/) (recommended): the commands run
  `uv run --with build123d python ...`, which fetches build123d on first use and works
  with any Python version. Without uv, `pip install build123d` into a venv.
- A slicer for your printer. The default bed is an **Elegoo Neptune 4 Pro**
  (220 x 220 x 260 mm usable); every script takes `--bed XxYxZ` for another printer.

## Installation

```bash
/plugin marketplace add ihistand/claude-plugins
/plugin install stl-generator-toolkit@ihistand
```

For development, from a local clone:

```bash
/plugin marketplace add /path/to/claude-plugins
/plugin install stl-generator-toolkit@ihistand
```

## Layout

```
stl-generator-toolkit/
├── .claude-plugin/plugin.json
├── commands/                      # the four slash commands above
└── skills/stl-generator/          # synced from ihistand/claude-skills; don't edit here
    ├── SKILL.md
    ├── references/                # printer_specs.md, build123d_patterns.md
    └── scripts/                   # circle_cutting_jig, angle_wedge, spacing_block, printcheck
```
