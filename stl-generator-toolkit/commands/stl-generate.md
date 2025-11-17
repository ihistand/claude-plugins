---
description: Generate custom 3D printable STL files for woodworking jigs
---

You are generating a custom STL file for 3D printing using the stl-generator skill.

**Workflow:**

1. Invoke the stl-generator skill
2. Ask the user what type of jig or fixture they need
3. Gather requirements:
   - Dimensions and specifications
   - Functional requirements
   - Any special features needed
4. Check if a pre-built script exists (circle cutting jig, angle wedge, spacing block)
5. If pre-built script exists:
   - Run the appropriate script with user's parameters
   - Move STL to `/mnt/user-data/outputs/`
6. If custom design needed:
   - Write CadQuery code following patterns from references
   - Export STL file
   - Move to `/mnt/user-data/outputs/`
7. Provide download link and print settings recommendations

**Critical**: Always verify design fits within 225×225×265mm build volume (Elegoo Neptune 4 Pro).
