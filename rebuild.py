#!/usr/bin/env python3
"""Rebuild uno-guardians-of-the-deep.html from template + assets."""
import os, base64

def rebuild():
    # Read template
    with open('src/template.html', 'r') as f:
        html = f.read()
    
    # Scan assets directory for all WebP files
    assets_dir = 'assets'
    assets = {}
    for fname in os.listdir(assets_dir):
        if fname.endswith('.webp'):
            key = fname.replace('.webp', '')
            assets[key] = os.path.join(assets_dir, fname)
    
    # Inline all assets as base64 data URIs
    inlined = 0
    for key, path in sorted(assets.items()):
        placeholder = f'{{{{A:{key}}}}}'
        if placeholder in html:
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')
            uri = f'data:image/webp;base64,{data}'
            html = html.replace(placeholder, uri)
            kb = len(data) // 1024
            print(f"  ✓ {key}: {kb}KB")
            inlined += 1
        else:
            print(f"  - {key}: no placeholder in template")
    
    # Write final file
    os.makedirs('.', exist_ok=True)
    with open('uno-guardians-of-the-deep.html', 'w') as f:
        f.write(html)
    
    size_kb = os.path.getsize('uno-guardians-of-the-deep.html') // 1024
    print(f"\n✅ Rebuilt {inlined} assets → uno-guardians-of-the-deep.html ({size_kb}KB)")

if __name__ == '__main__':
    rebuild()
