#!/usr/bin/env python3
"""Process UNO character art: background removal for swimmers, resize/compress everything."""
import cv2, numpy as np, os
from PIL import Image

SRC = "/root/.claude/uploads/3a0658d9-0b08-5ddc-9694-5c94efb459e0"
OUT = "/home/claude/uno-site/assets"
os.makedirs(OUT, exist_ok=True)

# ---------- background removal via neighbor-relative flood fill ----------
def cutout(path, out_name, max_side=1400, out_side=900, lo=6, up=6, quality=80,
           extra_seeds=None, erode=1, blur=1.5):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    scale = min(1.0, max_side / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    # slight blur to tame texture noise before flood fill
    ff_img = cv2.bilateralFilter(img, 5, 30, 30)
    mask = np.zeros((h+2, w+2), np.uint8)
    seeds = [(2,2), (w-3,2), (2,h-3), (w-3,h-3),
             (w//2, 2), (2, h//2), (w-3, h//2), (w//4, 2), (3*w//4, 2)]
    if extra_seeds: seeds += extra_seeds
    flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY
    for s in seeds:
        sx = min(max(s[0],0), w-1); sy = min(max(s[1],0), h-1)
        if mask[sy+1, sx+1]: continue
        cv2.floodFill(ff_img.copy(), mask, (sx, sy), 0, (lo,)*3, (up,)*3, flags)
    bg = mask[1:-1, 1:-1]
    alpha = 255 - bg
    # remove small foreground specks
    n, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), 8)
    if n > 1:
        big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        keep = np.zeros_like(alpha)
        for i in range(1, n):
            if i == big or stats[i, cv2.CC_STAT_AREA] > 0.001 * h * w:
                keep[labels == i] = 255
        alpha = keep
    if erode:
        alpha = cv2.erode(alpha, np.ones((3,3), np.uint8), iterations=erode)
    if blur:
        alpha = cv2.GaussianBlur(alpha, (0,0), blur)
    # crop to content bbox with margin
    ys, xs = np.where(alpha > 8)
    if len(ys):
        m = 6
        y0, y1 = max(0, ys.min()-m), min(h, ys.max()+m)
        x0, x1 = max(0, xs.min()-m), min(w, xs.max()+m)
        img, alpha = img[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
    h2, w2 = img.shape[:2]
    s2 = min(1.0, out_side / max(h2, w2))
    if s2 < 1.0:
        img = cv2.resize(img, (int(w2*s2), int(h2*s2)), interpolation=cv2.INTER_AREA)
        alpha = cv2.resize(alpha, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    rgba[:, :, 3] = alpha
    pim = Image.fromarray(rgba)
    p = os.path.join(OUT, out_name)
    pim.save(p, "WEBP", quality=quality, method=6)
    fg = (alpha > 128).mean()
    print(f"{out_name}: {pim.size} fg={fg:.2f} {os.path.getsize(p)//1024}KB")

# ---------- plain resize ----------
def resize(path, out_name, out_w=None, out_h=None, quality=80):
    im = Image.open(path).convert("RGBA" if path.endswith("png") and "3437" in path else "RGB")
    w, h = im.size
    if out_w: s = out_w / w
    else: s = out_h / h
    if s < 1.0:
        im = im.resize((int(w*s), int(h*s)), Image.LANCZOS)
    p = os.path.join(OUT, out_name)
    im.save(p, "WEBP", quality=quality, method=6)
    print(f"{out_name}: {im.size} {os.path.getsize(p)//1024}KB")

# swimmers (cutouts)
cutout(f"{SRC}/b7251940-Uno.png",    "uno-side.webp",  out_side=1000, lo=5, up=5)
cutout(f"{SRC}/7b254491-Whales.png", "whale.webp",     out_side=1000, lo=7, up=7)
cutout(f"{SRC}/6dd8df99-Turtle.png", "turtle.webp",    out_side=900,  lo=6, up=6)
cutout(f"{SRC}/6e57bc6e-Puffy.png",  "puffy.webp",     out_side=800,  lo=6, up=6)
cutout(f"{SRC}/866eafba-Mantas.png", "mantas.webp",    out_side=800,  lo=6, up=6)

# cute uno already transparent
im = Image.open(f"{SRC}/34f37393-911d8d49b6db4463aadffc725a72bb75.png").convert("RGBA")
bbox = im.getbbox(); im = im.crop(bbox)
im.thumbnail((900, 900), Image.LANCZOS)
im.save(f"{OUT}/uno-hero.webp", "WEBP", quality=84, method=6)
print(f"uno-hero.webp: {im.size} {os.path.getsize(OUT+'/uno-hero.webp')//1024}KB")

# portrait cards (keep bg)
resize(f"{SRC}/94bbbe47-Sarah.png",     "sarah.webp",     out_h=820, quality=80)
resize(f"{SRC}/79df1c2d-Professor.png", "elias.webp",     out_h=820, quality=80)
resize(f"{SRC}/f1d06aca-Marty.png",     "marty.webp",     out_h=820, quality=80)
resize(f"{SRC}/020970af-Ivanka.png",    "ivanka.webp",    out_w=1000, quality=80)
resize(f"{SRC}/a4956f3f-Seals.jpg",     "seals.webp",     out_w=900, quality=80)

# scenes
resize(f"{SRC}/362ef93b-Temple.png",    "temple.webp",    out_w=1600, quality=76)
resize(f"{SRC}/aa31b768-UNO_4K.png",    "poster.webp",    out_w=1500, quality=80)

# montage of cutouts over checkerboard for visual QA
def board(size):
    t = 24
    b = np.zeros((size[1], size[0], 3), np.uint8)
    for y in range(0, size[1], t):
        for x in range(0, size[0], t):
            c = 200 if ((x//t + y//t) % 2 == 0) else 120
            b[y:y+t, x:x+t] = c
    return Image.fromarray(b)

names = ["uno-side.webp","whale.webp","turtle.webp","puffy.webp","mantas.webp","uno-hero.webp"]
cell = 420
mont = board((cell*3, cell*2))
for i, nm in enumerate(names):
    im = Image.open(os.path.join(OUT, nm)).convert("RGBA")
    im.thumbnail((cell-16, cell-16), Image.LANCZOS)
    x = (i % 3) * cell + (cell - im.size[0])//2
    y = (i // 3) * cell + (cell - im.size[1])//2
    mont.paste(im, (x, y), im)
mont.save("/home/claude/uno-site/montage.png")
total = sum(os.path.getsize(os.path.join(OUT,f)) for f in os.listdir(OUT))
print(f"TOTAL assets: {total//1024}KB")
