---
description: Generate circle cutting jig for router work
---

You are generating a circle cutting jig STL file using the stl-generator skill and pre-built script.

**Workflow:**

1. Invoke the stl-generator skill
2. Ask the user for:
   - Outer diameter (mm)
   - Inner diameter (mm)
   - Optional: output filename
3. Run the circle cutting jig script:
   ```bash
   python /home/ivan/ihistand-projects/claude-plugins/stl-generator-toolkit/scripts/circle_cutting_jig.py <outer_diameter> <inner_diameter> output.stl
   ```
4. Move STL to `/mnt/user-data/outputs/`
5. Provide:
   - Download link: `[View your file](computer:///mnt/user-data/outputs/filename.stl)`
   - Dimensions summary
   - Suggested print settings (3-4 perimeter walls, 20% infill)

**Use case**: Perfect for lampshade rings, circular frames, and router compass cutting.
