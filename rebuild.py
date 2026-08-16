#!/usr/bin/env python3
"""Rebuild production HTML from template + assets.

Web builds reference /assets/*.webp so browsers can cache and load in
parallel. The offline deliverable still inlines images as data URIs.
"""
import os, base64

def rebuild():
    with open('src/template.html', 'r') as f:
        template = f.read()

    assets_dir = 'assets'
    keys = []
    for fname in sorted(os.listdir(assets_dir)):
        if fname.endswith('.webp'):
            keys.append(fname.replace('.webp', ''))

    web = template
    offline = template
    for key in keys:
        placeholder = f'{{{{A:{key}}}}}'
        if placeholder not in template:
            print(f"  - {key}: no placeholder in template")
            continue
        path = os.path.join(assets_dir, key + '.webp')
        web = web.replace(placeholder, f'/assets/{key}.webp')
        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('ascii')
        offline = offline.replace(placeholder, f'data:image/webp;base64,{data}')
        print(f"  ✓ {key}: {os.path.getsize(path)//1024}KB")

    os.makedirs('.', exist_ok=True)
    with open('index.html', 'w') as f:
        f.write(web)
    with open('uno-guardians-of-the-deep.html', 'w') as f:
        f.write(offline)

    print(f"\n✅ Web index.html {os.path.getsize('index.html')//1024}KB · offline HTML {os.path.getsize('uno-guardians-of-the-deep.html')//1024}KB")

if __name__ == '__main__':
    rebuild()
