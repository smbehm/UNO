# Publishing to GitHub

## Quick Setup

1. **Create a new GitHub repository** (e.g., `uno-guardians-of-the-deep`)
2. **Extract the zip file** you downloaded
3. **Initialize git** in the directory:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: UNO website"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/uno-guardians-of-the-deep.git
   git push -u origin main
   ```

## Vercel Deployment (uno-x.world)

This repo is already connected to Vercel (`uno-ashy.vercel.app`) with the custom domain **uno-x.world**.

Vercel serves `/` from `index.html`. `vercel.json` also rewrites `/` to `uno-guardians-of-the-deep.html`, so the homepage works either way.

Push to `main` and Vercel will redeploy automatically. After a successful deploy:

- https://uno-x.world
- https://www.uno-x.world
- https://uno-ashy.vercel.app

If the custom domain ever shows a Vercel 404 while those URLs work, confirm in the Vercel dashboard that `uno-x.world` and `www.uno-x.world` are attached to this project.

## GitHub Pages Deployment

To host this on GitHub Pages:

1. **Go to Settings → Pages**
2. **Source**: Deploy from a branch → `main`
3. **Folder**: root `/`
4. **Wait 1-2 minutes** for deployment
5. **Access** at: `https://YOUR_USERNAME.github.io/UNO/`

Your landing page will be live and publicly accessible (`index.html` is the homepage).

## File Structure in Repository

```
uno-guardians-of-the-deep/
├── index.html                       ← Homepage for Vercel / GitHub Pages
├── uno-guardians-of-the-deep.html   ← Main deliverable (1.7MB)
├── vercel.json                      ← Rewrites "/" to the homepage
├── README.md                         ← Project overview
├── GITHUB_SETUP.md                   ← This file
├── rebuild.py                        ← Update script
├── .gitignore                        ← Ignore build artifacts
├── .gitattributes                    ← Line ending config
├── src/
│   ├── template.html                 ← HTML source
│   └── process.py                    ← Image optimization pipeline
└── assets/                           ← WebP images (1.2MB)
    ├── keyart.webp, logo.webp
    ├── uno-hero.webp, uno-side.webp, whale.webp
    ├── turtle.webp, puffy.webp, mantas.webp, krabby.webp
    └── sarah.webp, elias.webp, marty.webp, ivanka.webp
```

## Updating Content

**To edit text/copy**:
1. Modify `src/template.html`
2. Run `python rebuild.py`
3. Commit and push:
   ```bash
   git add .
   git commit -m "Update: change character bios"
   git push
   ```
   GitHub Pages will auto-deploy within 1-2 minutes.

**To replace an image**:
1. Save new image to `assets/`
2. Run `python src/process.py` to optimize it
3. Run `python rebuild.py` to rebuild
4. Commit and push (as above)

## Performance Notes

- **1.7MB single file**: Contains all images as base64-encoded data URIs
- **No external dependencies**: Download and open offline (file://)
- **Mobile-optimized**: Responsive design, hardware-accelerated WebGL
- **Best browser support**: Chrome, Firefox, Safari, Edge

## Troubleshooting

**Page won't load / Vercel 404 on /**:
- Verify `index.html` exists in the repository root
- Confirm `vercel.json` rewrites `/` to `uno-guardians-of-the-deep.html`
- Direct file URL still works: `/uno-guardians-of-the-deep.html`
- Check browser console (F12) for errors
- Try a different browser (Chrome recommended)

**Images not showing**:
- Ensure `assets/` folder is in the same directory
- Rebuild with `python rebuild.py`
- Commit `.html` and push again

**Rebuild fails**:
- Ensure `src/template.html` and `assets/*.webp` exist
- Run `python rebuild.py` from the root directory
- Check for Python 3.6+

## Questions?

See the main README.md for development details, asset optimization info, and browser compatibility.
