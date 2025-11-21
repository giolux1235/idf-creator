# Images Directory

This directory contains images used in the IDF Creator documentation and README.

## 📁 Directory Structure

```
docs/assets/images/
├── buildings/          # Building-related images
│   ├── building-example.png
│   ├── building-types.png
│   └── example-building-model.png
├── workflow/          # Workflow and process diagrams
│   └── idf-creator-workflow.png
└── README.md         # This file
```

## 🖼️ Image Guidelines

### Recommended Images

#### Building Images (`buildings/`)
1. **`building-example.png`** (1200x600px)
   - Showcase different building types (office, residential, retail)
   - Professional building photography or 3D renderings
   - Can use stock photos from Unsplash/Pexels (with attribution)

2. **`building-types.png`** (1200x400px)
   - Visual representation of supported building types
   - Icons or illustrations for each type
   - Can be a collage or grid layout

3. **example-building-model.png** (1200x600px)
   - 3D visualization of a generated building model
   - EnergyPlus visualization or 3D rendering
   - Shows zones, surfaces, or energy flow

#### Workflow Images (`workflow/`)
1. **`idf-creator-workflow.png`** (1200x800px)
   - Flowchart showing the IDF creation process
   - Input → Processing → Output visualization
   - Can be created with Draw.io, Mermaid, or similar tools

### Image Sources

#### Free Stock Photos
- **Unsplash**: https://unsplash.com/s/photos/building
  - Search: "office building", "residential building", "commercial building"
  - Free to use with attribution
  
- **Pexels**: https://www.pexels.com/search/building/
  - Free stock photos
  - No attribution required

#### Creating Diagrams
- **Draw.io**: https://app.diagrams.net/
  - Create workflow diagrams
  - Export as PNG or SVG

- **Mermaid**: https://mermaid.live/
  - Code-based diagrams
  - Can be rendered directly in GitHub

### Image Specifications

- **Format**: PNG or JPG
- **Width**: 1200px (recommended for README)
- **Aspect Ratio**: 2:1 or 3:2 for building images
- **File Size**: Keep under 500KB for web performance
- **Optimization**: Use tools like TinyPNG or ImageOptim

### Adding Images

1. **Download or create** your image
2. **Optimize** the image (compress if needed)
3. **Place** in the appropriate directory (`buildings/` or `workflow/`)
4. **Reference** in README.md using the path: `docs/assets/images/[directory]/[filename]`

### Example Image References

```markdown
![Alt text](docs/assets/images/buildings/building-example.png)
```

### Attribution

If using images from external sources:
- Add attribution in the image filename or README
- Example: `building-example-unsplash.jpg`
- Include photographer credit if required

## 🎨 Image Ideas

### Building Types Visualization
- Office buildings (modern glass facades)
- Residential buildings (apartments, houses)
- Retail buildings (stores, malls)
- Industrial buildings (warehouses, factories)

### Process Visualization
- Before/after: Manual vs. Automated IDF creation
- Workflow diagram: Address → IDF → Simulation
- Architecture diagram: System components

### Results Visualization
- Energy consumption charts
- Building model 3D renderings
- Simulation results visualization

## 📝 Notes

- Images are referenced in README.md
- Keep images optimized for web
- Use descriptive filenames
- Consider creating a `.gitkeep` file if directories are empty

