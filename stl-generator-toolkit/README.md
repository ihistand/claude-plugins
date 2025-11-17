# STL Generator Toolkit

Comprehensive toolkit for generating 3D printable STL files for woodworking jigs and fixtures using CadQuery. Optimized for Elegoo Neptune 4 Pro with engineering best practices and pre-built parametric scripts.

## What's Included

### Skills

**stl-generator** - Complete guide for 3D printable woodworking jig design that includes:
- Pre-built scripts for common jigs (circle cutting, angle wedges, spacing blocks)
- CadQuery parametric design patterns
- Printer-specific constraints (Elegoo Neptune 4 Pro: 225×225×265mm)
- Structural integrity and printability best practices
- Hardware integration guidelines
- Reference files for design patterns and printer specifications

### Slash Commands

**`/stl-generate`** - Generate custom STL files for any woodworking jig:
- Ask user for requirements and dimensions
- Use pre-built scripts when applicable
- Write custom CadQuery code for unique designs
- Export and provide download links

**`/stl-circle-jig`** - Quick generation of circle cutting jigs:
- Router jigs for perfect circles
- Ideal for lampshade rings and circular frames
- Adjustable inner/outer diameters

**`/stl-angle-wedge`** - Generate angle guide wedges:
- Compound miter cuts and angled assembly
- Any angle from 1-60 degrees
- Embossed angle labels for easy identification

**`/stl-spacing-block`** - Create precision spacing blocks:
- Single blocks or matched sets
- Embossed dimension labels
- Finger relief cutouts for easy handling

## Installation

### Option 1: Install from Marketplace

```bash
# Add marketplace
/plugin marketplace add ihistand/claude-plugins

# Install plugin
/plugin install stl-generator-toolkit@ihistand
```

### Option 2: Install from Local Directory

```bash
# Add marketplace locally
/plugin marketplace add /path/to/claude-plugins

# Install plugin
/plugin install stl-generator-toolkit@dev
```

Then restart Claude Code.

## Usage Examples

### Generate a Circle Cutting Jig

```
User: I need a jig for cutting a 300mm diameter lampshade ring with 250mm inner diameter
Claude: /stl-circle-jig
[Generates jig with specified dimensions]
```

### Create an Angle Wedge

```
User: I need a 22.5 degree angle guide for octagon assembly
Claude: /stl-angle-wedge
[Generates wedge with embossed angle marking]
```

### Generate Spacing Blocks

```
User: I need spacing blocks for 5mm, 10mm, and 15mm gaps
Claude: /stl-spacing-block
[Generates set of three labeled spacing blocks]
```

### Custom Jig Design

```
User: I need a custom router template for mortising
Claude: /stl-generate
[Gathers requirements and writes custom CadQuery code]
```

## Target Printer Specifications

- **Printer**: Elegoo Neptune 4 Pro
- **Build Volume**: 225mm × 225mm × 265mm
- **Layer Height**: 0.2mm standard
- **Units**: Metric (millimeters)

All designs are optimized for this printer's capabilities and constraints.

## Pre-Built Scripts

The plugin includes three production-ready Python scripts:

| Script | Purpose | Parameters |
|--------|---------|------------|
| `circle_cutting_jig.py` | Router jigs for perfect circles | outer_diameter, inner_diameter |
| `angle_wedge.py` | Angle guide wedges | angle_degrees (1-60°) |
| `spacing_block.py` | Precision spacing blocks | height (single) or set of heights |

**Location**: `stl-generator-toolkit/scripts/`

## Design Best Practices

### Structural Integrity

- **Wall thickness**: 3-4 perimeter walls for strength
- **Base thickness**: Minimum 5mm for flatness
- **Chamfers/fillets**: 1-2mm to reduce stress concentrations
- **Layer orientation**: Perpendicular to primary load direction

### Printability

- **Overhangs**: Keep under 45° to avoid supports
- **Bridges**: Avoid unsupported spans over 30mm
- **Orientation**: Largest flat surface on print bed
- **Draft angles**: 0.2mm for nesting parts

### Woodworking Functionality

- **Reference surfaces**: Smooth, no text on work contact areas
- **Alignment marks**: Visual indicators (notches, text, contrasting surfaces)
- **Finger reliefs**: Easy handling for small parts
- **Clamping access**: 25mm+ clearance

### Hardware Integration

Common hole sizes (add 0.3-0.5mm clearance):
- M3: 3.3mm hole
- M4: 4.3mm hole
- M5: 5.3mm hole
- #8 wood screw: 4.5mm hole
- 1/4"-20 bolt: 6.6mm hole

## CadQuery Quick Reference

**Basic structure**:
```python
import cadquery as cq

# Create base
part = cq.Workplane("XY").box(50, 30, 10)

# Add features
part = (
    part.faces(">Z")
    .workplane()
    .circle(5)
    .cutThruAll()
)

# Export
cq.exporters.export(part, "output.stl")
```

**Essential methods**:
- `.box(w, d, h)` - rectangular solid
- `.circle(r)` - circle sketch
- `.extrude(height)` - extrude 2D to 3D
- `.cutThruAll()` - cut through entire part
- `.fillet(radius)` - round edges
- `.chamfer(distance)` - bevel edges

For detailed patterns, see `references/cadquery_patterns.md`.

## Common Jig Types

### Lampshade Jigs
- Circle cutting for ring frames
- Angle guides for tapered shades
- Spacing blocks for consistent rib spacing

### Router Jigs
- Edge guides with adjustable fence
- Template guides (16mm OD standard)
- Bit clearance slots (7-8mm for 1/4" shanks)

### Assembly Jigs
- Right angle corner blocks
- Spacing sets for consistent gaps
- Alignment pins (6mm diameter, 10mm height)

### Clamping Aids
- Flat cauls with finger reliefs
- Pressure distributors
- Sacrificial clamp blocks

## File Organization

STL files are automatically moved to `/mnt/user-data/outputs/` for easy access and download.

**Naming convention**:
- Good: `lampshade_jig_300mm_OD.stl`
- Good: `wedge_22.5_degrees.stl`
- Poor: `jig1.stl`

## Troubleshooting

### "Module 'cadquery' not found"
```bash
pip install --break-system-packages cadquery
```

### STL appears hollow in slicer
This is normal - slicers add infill during slicing. The generated STL is a surface model (shell).

### Features too small to print
- Check minimum feature size: 1.0mm
- Increase wall thickness to at least 2-3mm
- Verify hole diameters are >= 2mm

### Part doesn't fit on print bed
- Check dimensions against 220×220mm effective area
- Consider splitting large jigs into sections
- Rotate part to minimize footprint

## Reference Files

- **`references/printer_specs.md`** - Elegoo Neptune 4 Pro specifications and design constraints
- **`references/cadquery_patterns.md`** - Common CadQuery patterns and examples

Always read `printer_specs.md` when starting a new jig design.

## Official Documentation

- [CadQuery Documentation](https://cadquery.readthedocs.io/)
- [Elegoo Neptune 4 Pro Specifications](https://www.elegoo.com/products/elegoo-neptune-4-pro-fdm-3d-printer)
- [OpenSCAD Documentation](https://openscad.org/documentation.html) (alternative CAD tool)

## License

Created by Ivan Histand (ihistand@rotoplas.com)

## Contributing

This plugin follows engineering best practices:
- All designs must fit within printer build volume
- Minimum feature sizes must be printable (≥1.0mm)
- Include structural integrity considerations
- Provide clear dimension labels and markings
- Test scripts before committing
- Document new jig patterns in references

For questions or contributions, contact Ivan Histand.
