---
description: Generate precision spacing blocks for assembly
---

You are generating spacing block STL file(s) using the stl-generator skill and pre-built script.

**Workflow:**

1. Invoke the stl-generator skill
2. Ask the user for spacing requirements:
   - Single block: height (required), width, depth
   - Set of blocks: comma-separated heights (e.g., "5,10,15,20")
   - Optional: output filename
3. Run the spacing block script:
   ```bash
   # Single block
   python /home/ivan/ihistand-projects/claude-plugins/stl-generator-toolkit/scripts/spacing_block.py <height_mm> [width_mm] [depth_mm] output.stl

   # Set of blocks
   python /home/ivan/ihistand-projects/claude-plugins/stl-generator-toolkit/scripts/spacing_block.py set <h1>,<h2>,<h3> output.stl
   ```
4. Move STL to `/mnt/user-data/outputs/`
5. Provide:
   - Download link: `[View your file](computer:///mnt/user-data/outputs/filename.stl)`
   - Block dimensions
   - Suggested print settings (100% infill for accuracy, 4 perimeters)

**Use case**: Consistent assembly gaps, router bit height setup, dado spacing verification.
