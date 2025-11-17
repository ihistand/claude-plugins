---
description: Generate angle guide wedge for compound cuts
---

You are generating an angle wedge STL file using the stl-generator skill and pre-built script.

**Workflow:**

1. Invoke the stl-generator skill
2. Ask the user for:
   - Angle in degrees (1-60°)
   - Optional: output filename
3. Run the angle wedge script:
   ```bash
   python /home/ivan/ihistand-projects/claude-plugins/stl-generator-toolkit/scripts/angle_wedge.py <angle_degrees> output.stl
   ```
4. Move STL to `/mnt/user-data/outputs/`
5. Provide:
   - Download link: `[View your file](computer:///mnt/user-data/outputs/filename.stl)`
   - Angle confirmation
   - Suggested print settings (orient flat side on bed, no supports needed)

**Use case**: Compound miter cuts, angled assembly work, saw blade setup verification.
