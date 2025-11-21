# Image Sources Guide

This guide helps you find and add building images to the IDF Creator repository.

## 🎯 Quick Start

1. **Find images** using the sources below
2. **Download** and optimize them (compress if needed)
3. **Place** in `docs/assets/images/buildings/` or `docs/assets/images/workflow/`
4. **Reference** in README.md (already set up with placeholders)

## 📸 Recommended Image Sources

### Free Stock Photos (No Attribution Required)

#### Pexels
- **URL**: https://www.pexels.com/search/building/
- **Search Terms**: 
  - "office building"
  - "commercial building"
  - "residential building"
  - "modern architecture"
- **License**: Free for commercial use, no attribution required
- **Download**: Click download → Original size

#### Pixabay
- **URL**: https://pixabay.com/images/search/building/
- **License**: Free for commercial use
- **Good for**: High-quality building photos

### Free Stock Photos (Attribution Required)

#### Unsplash
- **URL**: https://unsplash.com/s/photos/building
- **Search Terms**: 
  - "office building exterior"
  - "commercial building"
  - "skyscraper"
  - "modern building"
- **License**: Free to use, attribution appreciated
- **Note**: Add photographer credit if using

### Creating Your Own Images

#### Building Visualizations
- **EnergyPlus**: Use EnergyPlus visualization tools to create building model images
- **SketchUp**: Create simple 3D building models
- **Blender**: Free 3D modeling software for building visualizations

#### Workflow Diagrams
- **Draw.io**: https://app.diagrams.net/
  - Create professional flowcharts
  - Export as PNG (1200px width)
  - Free and easy to use

- **Mermaid**: https://mermaid.live/
  - Code-based diagrams
  - Can be rendered directly in GitHub markdown
  - No image file needed!

## 🖼️ Image Specifications

### Building Images
- **Size**: 1200x600px (2:1 ratio) or 1200x800px
- **Format**: PNG or JPG
- **File Size**: Under 500KB (optimize with TinyPNG)
- **Content**: Professional building photos, 3D renderings, or illustrations

### Workflow Diagrams
- **Size**: 1200x800px or wider
- **Format**: PNG (for diagrams)
- **Content**: Flowcharts showing the IDF creation process

## 📋 Image Checklist

For each image you add:

- [ ] Image is relevant and adds value
- [ ] Image is properly sized (1200px width recommended)
- [ ] Image is optimized (compressed if needed)
- [ ] Image has descriptive filename
- [ ] Image is placed in correct directory
- [ ] Image is referenced in README.md
- [ ] Attribution added (if required by license)

## 🎨 Specific Image Ideas

### Hero Image (`hero-building.png`)
- Modern office building or skyscraper
- Professional, clean aesthetic
- Represents energy modeling/analysis
- **Example searches**: "modern office building", "glass skyscraper"

### Building Types (`building-types.png`)
- Grid or collage showing different building types:
  - Office building
  - Residential building
  - Retail store
  - Warehouse
- Can create as a composite image or use icons

### Example Building Model (`example-building-model.png`)
- 3D visualization of a building model
- EnergyPlus visualization output
- Building zones or energy flow visualization
- **Tools**: EnergyPlus, SketchUp, Blender

### Workflow Diagram (`idf-creator-workflow.png`)
- Flowchart: Address → Location Processing → Document Parsing → IDF Generation → Simulation
- Use Draw.io or Mermaid
- Include icons for each step

## 🛠️ Image Optimization Tools

### Online Tools
- **TinyPNG**: https://tinypng.com/ - Compress PNG/JPG images
- **Squoosh**: https://squoosh.app/ - Google's image compression tool
- **ImageOptim**: https://imageoptim.com/ - Mac app for image optimization

### Command Line
```bash
# Using ImageMagick (if installed)
convert input.jpg -resize 1200x600 -quality 85 output.jpg

# Using pngquant (for PNG)
pngquant --quality=65-80 input.png
```

## 📝 Adding Images - Step by Step

1. **Find or create** your image
   - Use Pexels/Unsplash for photos
   - Use Draw.io for diagrams
   - Use EnergyPlus for building visualizations

2. **Optimize** the image
   - Resize to 1200px width
   - Compress with TinyPNG
   - Ensure file size < 500KB

3. **Save** with descriptive filename
   - Example: `building-example.png`
   - Use lowercase, hyphens for spaces

4. **Place** in correct directory
   - Building images → `docs/assets/images/buildings/`
   - Workflow diagrams → `docs/assets/images/workflow/`

5. **Verify** README.md references
   - Images are already referenced in README.md
   - Just add the actual image files!

## 🔗 Quick Links

- **Pexels Buildings**: https://www.pexels.com/search/building/
- **Unsplash Buildings**: https://unsplash.com/s/photos/building
- **Draw.io**: https://app.diagrams.net/
- **Mermaid Live**: https://mermaid.live/
- **TinyPNG**: https://tinypng.com/

## 💡 Tips

- **Start with Pexels** - Easiest, no attribution needed
- **Use consistent style** - All building images should have similar aesthetic
- **Keep it professional** - Clean, modern building photos work best
- **Optimize for web** - Smaller file sizes = faster page loads
- **Test in README** - View how images look in the actual README

---

**Need help?** Check the main [README.md](../../../README.md) or open an issue on GitHub.

