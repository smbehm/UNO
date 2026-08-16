# UNO: Guardians of the Deep

A WebGL-powered interactive landing page for the animated film *UNO: Guardians of the Deep*. 

## Features

- **Raw WebGL Ocean**: Procedural gradient depth, animated caustics, god rays, and particle effects
- **Interactive Scroll Parallax**: Characters swim and dive as you scroll (GSAP ScrollTrigger)
- **Self-Contained Single File**: All assets base64-encoded—download and open locally (file://) 
- **Mobile Responsive**: Adapts to all screen sizes with optimized performance
- **YouTube Integration**: Embedded trailer with reachability detection and file:// fallback

## Live site

The production site is served by Vercel:

- **https://uno-x.world**
- **https://www.uno-x.world**
- https://uno-ashy.vercel.app

Vercel (and GitHub Pages) serve `/` from `index.html`. The self-contained deliverable is also available as `uno-guardians-of-the-deep.html`. After editing, run `rebuild.py` so both files stay in sync.

## Quick Start

1. Open https://uno-x.world — or download `index.html` / `uno-guardians-of-the-deep.html`
2. Open the HTML file in any modern browser (Chrome, Firefox, Safari, Edge)
3. No installation or dependencies required for the local file

## Development

### File Structure
```
.
├── index.html                         # Production homepage for Vercel / GitHub Pages
├── uno-guardians-of-the-deep.html     # Same self-contained deliverable (1.7MB)
├── vercel.json                        # Serves "/" as the homepage
├── src/
│   ├── template.html                  # HTML template with placeholders
│   ├── app.js                         # WebGL engine (integrated into template)
│   └── process.py                     # Image processing pipeline
├── assets/                            # WebP optimized images (14 files)
│   ├── uno-hero.webp, whale.webp, turtle.webp, ...
│   └── keyart.webp, poster.webp (same content, CSS-referenced)
└── rebuild.py                         # Rebuild script for asset updates
```

### Editing Content

**To update text** (character bios, act names, etc.):
1. Edit `src/template.html`
2. Run `rebuild.py`
3. Deploy the updated `index.html` (and `uno-guardians-of-the-deep.html`)

**To replace an image**:
1. Add new image to `assets/`
2. Run `process.py` to optimize (flood-fill alpha keying, WebP q80-84, auto-crop to bbox)
3. Run `rebuild.py`

### Image Processing Pipeline

```bash
python process.py
```

- Crop to alpha bbox (transparent background removal)
- Resize to display dimensions (max 1500px)
- Encode as WebP q80-84 (50-100KB typical)
- Compresses 14 images → ~1.2MB
- Creates montage.png for visual QA

### Rebuilding HTML

```bash
python rebuild.py
```

Scans `assets/`, inlines all WebP images as base64 data URIs, writes `uno-guardians-of-the-deep.html` (~1.7MB).

## Testing

### Local Testing
```bash
open uno-guardians-of-the-deep.html  # macOS
firefox uno-guardians-of-the-deep.html  # Linux/Windows
```

### Automated Tests
```bash
python test.py  # Playwright-based: loads page, captures scrollshot series, checks for console errors
```

Generates:
- `shots/shot0.png` through `shot6.png` (scroll progression)
- Console error report
- WebGL context check
- HUD depth meter verification

## Browser Support

| Browser | Status |
|---------|--------|
| Chrome 90+ | ✓ Full support |
| Firefox 88+ | ✓ Full support |
| Safari 14+ | ✓ Full support |
| Edge 90+ | ✓ Full support |
| Mobile Safari | ✓ Limited particles (perf) |
| Android Chrome | ✓ Limited particles (perf) |

## Performance

- **Desktop**: 60fps ocean + smooth scroll parallax
- **Mobile**: Reduced particle budget, auto-scaling particles based on device
- **CDN**: All assets self-contained—no external requests (fonts load via preconnect, trailer proxied)

## Asset Sizes

| Asset | Type | Size |
|-------|------|------|
| keyart | 16:9 poster/thumbnail | 247KB |
| logo | UNO wordmark + text | 344KB |
| uno-hero | dolphin centered | 155KB |
| uno-side | dolphin profile swim | 71KB |
| whale | threat character | 66KB |
| turtle | ancient one critter | 111KB |
| Others (9) | cast, seals, critters | 495KB |
| **Total HTML** | 1-file delivery | **1716KB** |

## Credits

- **Creative**: Fantasea Entertainment
- **Animation**: WebGL ocean shader + GSAP scroll engine
- **Character Art**: Flood-fill alpha keying + WebP optimization

## License

© 2026 FANTASEA. All rights reserved.
